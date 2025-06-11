\
import os
import json # Added for pretty printing
import pickle
from dotenv import load_dotenv

from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate # Explicitly using langchain_core.prompts

from app.rag.config import (
    DOTENV_PATH, # Still useful for fallback or if API key not passed
    FAISS_INDEX_PATH, # Will be passed via constructor, but needed for default
    EMBEDDING_MODEL_NAME, # Will be passed via constructor, but needed for default
    IMPORTANT_FIELDS,
    LLM_MODEL_NAME, # Will be passed via constructor, but needed for default
    LLM_TEMPERATURE, # Can remain a default or also be passed
    RETRIEVER_K
)
from app.models import Wine # For database model
from app.database import SessionLocal # For database session

class RAGPipeline:
    def __init__(self, openai_api_key: str | None = None, 
                 faiss_index_path: str = FAISS_INDEX_PATH, # Default to config if not provided
                 embedding_model_name: str = EMBEDDING_MODEL_NAME, # Default to config
                 llm_name: str = LLM_MODEL_NAME): # Default to config
        
        self.faiss_index_path = faiss_index_path
        self.embedding_model_name = embedding_model_name
        self.llm_name = llm_name
        
        if openai_api_key:
            self.api_key = openai_api_key
        else:
            self.api_key = self._load_openai_api_key_from_env() # Renamed for clarity

        self.embeddings = self._initialize_embeddings()
        self.vector_store = None # Initialized by load_vector_store or run_indexing
        self.qa_chain = None # Initialized by _initialize_qa_chain

    def _load_openai_api_key_from_env(self): # Renamed
        """Loads OpenAI API key from .env file if not provided to constructor."""
        load_dotenv(dotenv_path=DOTENV_PATH)
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print(f"Warning: OPENAI_API_KEY not found in {DOTENV_PATH} and not provided to constructor. This is required for the LLM.")
        return api_key

    def _initialize_embeddings(self):
        """Initializes HuggingFace embeddings using the model name from constructor."""
        print(f"Initializing embedding model: {self.embedding_model_name}...")
        try:
            return HuggingFaceEmbeddings(model_name=self.embedding_model_name)
        except Exception as e:
            print(f"Error initializing HuggingFaceEmbeddings: {e}")
            print("Please ensure 'sentence-transformers' and 'langchain-huggingface' are installed.")
            raise

    async def _load_wine_data_from_db(self):
        """Loads wine data from the PostgreSQL database."""
        print("Loading wine data from database...")
        wine_data_list = []
        async with SessionLocal() as session:
            async with session.begin():
                result = await session.execute(select(Wine))
                wines = result.scalars().all()
                for wine_model in wines:
                    wine_dict = {column.name: getattr(wine_model, column.name) for column in Wine.__table__.columns}
                    wine_data_list.append(wine_dict)
        print(f"Successfully loaded {len(wine_data_list)} wine records from the database.")
        return wine_data_list

    def _create_wine_documents(self, wine_data_list):
        """Creates LangChain Document objects from wine data."""
        documents = []
        for i, wine in enumerate(wine_data_list):
            page_content_parts = []
            metadata = {"source_db_id": wine.get("id", f"wine_db_item_{i}")}

            for field in IMPORTANT_FIELDS:
                value = wine.get(field)
                if value is not None:
                    value_str = ", ".join(map(str, value)) if isinstance(value, list) else str(value)
                    page_content_parts.append(f"{field.replace('_', ' ').capitalize()}: {value_str}")
            
            page_content = "\\\\n".join(page_content_parts)
            
            for key, val in wine.items():
                 if val is not None:
                    metadata[key] = val

            documents.append(Document(page_content=page_content, metadata=metadata))
        
        print(f"Created {len(documents)} documents for embedding.")
        return documents

    async def run_indexing(self):
        """Runs the full indexing pipeline: loads data, creates docs, embeds, and saves index."""
        print("Starting RAG pipeline indexing process (backend)...")
        
        wine_data = await self._load_wine_data_from_db()
        if not wine_data:
            print("No wine data loaded from database. Exiting indexing.")
            return

        langchain_documents = self._create_wine_documents(wine_data)
        if not langchain_documents:
            print("No documents created. Exiting indexing.")
            return

        if not self.embeddings:
            print("Embeddings not initialized. Exiting indexing.")
            return

        print("Creating FAISS vector store from documents...")
        try:
            self.vector_store = FAISS.from_documents(langchain_documents, self.embeddings)
            print("FAISS vector store created successfully.")
        except Exception as e:
            print(f"Error creating FAISS vector store: {e}")
            return
            
        print(f"Saving FAISS index to: {self.faiss_index_path}...")
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.faiss_index_path), exist_ok=True)
            self.vector_store.save_local(self.faiss_index_path)
            print(f"FAISS index saved successfully to {self.faiss_index_path}")
        except Exception as e:
            print(f"Error saving FAISS index: {e}")
            return
            
        print("RAG pipeline indexing process completed.")

    def load_vector_store(self):
        """Loads the FAISS index from local storage using path from constructor."""
        if not self.embeddings:
            # self._initialize_embeddings() # Already called in __init__
            if not self.embeddings: # Check if initialization failed
                print("Failed to initialize embeddings. Cannot load vector store.")
                return False

        if os.path.exists(self.faiss_index_path) and os.path.exists(os.path.join(self.faiss_index_path, "index.faiss")):
            print(f"Loading FAISS index from: {self.faiss_index_path}...")
            try:
                self.vector_store = FAISS.load_local(
                    self.faiss_index_path, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
                print("FAISS index loaded successfully.")
                return True
            except Exception as e:
                print(f"Error loading FAISS index: {e}")
                self.vector_store = None
                return False
        else:
            print(f"FAISS index not found at {self.faiss_index_path}. Run indexing first.")
            self.vector_store = None
            return False

    def _initialize_qa_chain(self):
        """Initializes the RetrievalQA chain using LLM name from constructor and a custom prompt."""
        if not self.vector_store:
            print("Vector store not loaded. Cannot initialize QA chain.")
            return False
        if not self.api_key:
            print("OpenAI API key not available. Cannot initialize LLM for QA chain.")
            return False

        print(f"Initializing LLM ({self.llm_name})...")
        try:
            llm = ChatOpenAI(
                openai_api_key=self.api_key, 
                model_name=self.llm_name, 
                temperature=LLM_TEMPERATURE
            )
        except Exception as e:
            print(f"Error initializing ChatOpenAI: {e}")
            return False

        # Custom prompt template - refined for clarity and instruction
        prompt_template_str = """
        You are an AI Sommelier. Your task is to recommend wines based on the user's query and the provided context.
        The context below contains information about several wines, including their name, varietal, description, food pairings, and other characteristics.
        Carefully review the user's question and the provided wine documents in the context.

        Instructions:
        1.  If the context contains specific wines that are a good match for the user's query (e.g., based on food pairing, description, wine type, or varietal), please recommend those wines. Mention their names and why they are a good fit based *only* on the provided context.
        2.  If the retrieved documents do not seem to directly or strongly match the user's specific request, clearly state that you couldn't find a specific wine for that exact request within the current selection using the provided documents.
        3.  In case no specific wine from the context is a clear match, you MAY offer a general wine pairing suggestion if it's appropriate for the type of query. For example, if the user asks for a wine for 'raclette' and no context wine explicitly mentions raclette, you could suggest general types of wine that traditionally pair well with raclette (e.g., a dry white wine from the Savoie region, a light-bodied red like Pinot Noir or Gamay, or a Swiss Chasselas). Clearly state that this is a general suggestion and not based on the specific wines in the context.
        4.  Do NOT invent details or make assumptions about wines that are not present in the context. Stick strictly to the information provided in the documents.
        5.  If the query is too vague or unanswerable even with a general suggestion, politely say so.
        6.  When recommending a wine from the context, refer to its details as found in the context.

        Context:
        {context}

        Question: {question}

        Helpful Answer (provide your recommendation or response here):
        """
        PROMPT = PromptTemplate(
            template=prompt_template_str, input_variables=["context", "question"]
        )

        print("Creating RetrievalQA chain with custom prompt...")
        try:
            retriever = self.vector_store.as_retriever(search_kwargs={"k": RETRIEVER_K})
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=llm,
                chain_type="stuff",
                retriever=retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT} # Added custom prompt
            )
            print("RetrievalQA chain created successfully with custom prompt.") # Added custom prompt note
            return True
        except Exception as e:
            print(f"Error during RetrievalQA chain creation with custom prompt: {e}") # Added custom prompt note
            return False

    async def query(self, user_query: str): # Changed to async def
        """Queries the RAG pipeline with a user question."""
        if not self.qa_chain:
            print("QA chain not initialized. Attempting to load vector store and initialize chain.")
            # These are synchronous calls, which is generally fine if they are not too long-running.
            # If FAISS loading or chain initialization becomes a bottleneck, they might need async versions
            # or to be run in a thread pool executor.
            if not self.load_vector_store():
                return {"error": "Failed to load vector store. Cannot query."}
            if not self._initialize_qa_chain():
                return {"error": "Failed to initialize QA chain. Cannot query."}
        
        print(f"Received query for RAG pipeline: {user_query}") # Clarified print
        try:
            result = await self.qa_chain.ainvoke({"query": user_query})
            
            return {
                "answer": result.get("result"),
                "source_documents": [
                    {
                        "page_content": doc.page_content,
                        "metadata": doc.metadata
                    } for doc in result.get("source_documents", []) # Use the already fetched docs
                ]
            }
        except Exception as e:
            print(f"Error during QA chain execution: {e}")
            return {"error": f"Error processing query: {e}"}

# Example usage (for testing, not typically run from here in production)
# if __name__ == '__main__':
#     # This part would need to be adapted to run an async function,
#     # e.g., using asyncio.run()
#     import asyncio
#     from app.config import get_settings

#     async def main_test():
#         settings = get_settings()
#         # Ensure OPENAI_API_KEY is loaded if you test this way
#         # You might need to explicitly load .env or ensure it's in your environment
#         # For example, by calling load_dotenv(DOTENV_PATH) here if settings don't pick it up
        
#         if not settings.OPENAI_API_KEY:
#             print("OPENAI_API_KEY not found in settings. Please ensure it's set in .env or environment.")
#             return

#         pipeline = RAGPipeline(openai_api_key=settings.OPENAI_API_KEY)
        
#         # 1. Run indexing if the index doesn't exist or needs update
#         # Check if index exists
#         if not os.path.exists(FAISS_INDEX_PATH) or not os.listdir(FAISS_INDEX_PATH):
#             print("FAISS index not found or empty, running indexing...")
#             await pipeline.run_indexing() # run_indexing is async
#         else:
#             print("FAISS index found, skipping indexing for test.")

#         # 2. Load the vector store and initialize QA chain (implicitly done by query if not ready)
#         # For explicit test:
#         # loaded = pipeline.load_vector_store()
#         # if loaded:
#         #     initialized = pipeline._initialize_qa_chain()
#         #     if not initialized:
#         #         print("Test: Failed to initialize QA chain after loading.")
#         #         return
#         # else:
#         #     print("Test: Failed to load vector store.")
#         #     return

#         # 3. Query the pipeline
#         test_query = "Suggest a light-bodied red wine for a summer evening."
#         print(f"\\nTesting query: '{test_query}'")
#         response = await pipeline.query(test_query) # query is now async
#         print("\\nQuery Response:")
#         print(json.dumps(response, indent=2))

#         another_query = "I want a full bodied white wine from Italy"
#         print(f"\\nTesting query: '{another_query}'")
#         response = await pipeline.query(another_query) # query is now async
#         print("\\nQuery Response:")
#         print(json.dumps(response, indent=2))

#     if __name__ == '__main__':
#         # This setup is needed to run the async main_test function
#         # Ensure that the environment (especially PYTHONPATH and .env loading) is correct
#         # when running this script directly.
#         # You might need to adjust sys.path if running from a different directory context.
#         # import sys
#         # sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        
#         # Load .env specifically for this test script if not handled by app.config.get_settings()
#         # This is because get_settings() might assume a certain working directory for .env.
#         # The DOTENV_PATH in rag.config should be absolute or correctly relative.
#         # load_dotenv(dotenv_path=DOTENV_PATH) # Ensure DOTENV_PATH is correct

#         asyncio.run(main_test())
