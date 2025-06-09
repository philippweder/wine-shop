\
import json
import os
import pickle
import argparse # New import
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.docstore.document import Document
from langchain_openai import ChatOpenAI # New import
from langchain.chains import RetrievalQA # New import

# --- Configuration ---
WINE_DATA_PATH = "/Users/weder/Documents/side_projects/wine-shop/lab/martel_wines.json"
# Path to the .env file in the backend directory
DOTENV_PATH = "/Users/weder/Documents/side_projects/wine-shop/backend/.env"
FAISS_INDEX_PATH = "/Users/weder/Documents/side_projects/wine-shop/lab/faiss_index_lab"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Fields to include in the document for embedding
IMPORTANT_FIELDS = [
    "name", "brandName", "varietal", "description", "food_pairing",
    "region", "sub_region", "type", "year", "alcohol_content", "price",
    "country", "aroma", "taste", "winemaking", "awards",
    "serving_temperature", "storage_potential"
]

# --- Helper Functions ---
def load_openai_api_key():
    """Loads OpenAI API key from .env file."""
    load_dotenv(dotenv_path=DOTENV_PATH)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Warning: OPENAI_API_KEY not found in .env file. This might be needed for querying later.")
    return api_key

def load_wine_data(file_path):
    """Loads wine data from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Successfully loaded {len(data)} wine records from {file_path}")
        return data
    except FileNotFoundError:
        print(f"Error: Wine data file not found at {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode JSON from {file_path}")
        return []

def create_wine_documents(wine_data_list):
    """Creates LangChain Document objects from wine data."""
    documents = []
    for i, wine in enumerate(wine_data_list):
        page_content_parts = []
        metadata = {"source": f"wine_data_item_{i}"} # Basic metadata

        for field in IMPORTANT_FIELDS:
            value = wine.get(field)
            if value: # Only include field if it has a value
                # For lists (like grape_variety, food_pairing), join them
                if isinstance(value, list):
                    value_str = ", ".join(map(str, value))
                else:
                    value_str = str(value)
                
                # Add to page content
                page_content_parts.append(f"{field.replace('_', ' ').capitalize()}: {value_str}")
                
                # Add to metadata if it's a key field for filtering (optional, but can be useful)
                # Example: metadata[field] = value_str 
        
        # Combine all parts into a single text string for embedding
        page_content = "\\n".join(page_content_parts)
        
        # Add other relevant fields to metadata
        for key, val in wine.items():
            if key not in IMPORTANT_FIELDS and val is not None: # Add other non-empty fields to metadata
                 metadata[key] = val
            elif key in ["name", "brandName", "type", "year", "country", "region", "price"]: # Ensure some key fields are in metadata
                 metadata[key] = wine.get(key)


        documents.append(Document(page_content=page_content, metadata=metadata))
    
    print(f"Created {len(documents)} documents for embedding.")
    return documents

# --- Main Indexing Pipeline ---
def run_indexing_pipeline(): # Renamed from main()
    print("Starting RAG pipeline indexing process...")
    
    # 1. Load API Key (optional for this stage but good practice)
    load_openai_api_key()
    
    # 2. Load wine data
    wine_data = load_wine_data(WINE_DATA_PATH)
    if not wine_data:
        print("No wine data loaded. Exiting.")
        return
        
    # 3. Create documents for LangChain
    langchain_documents = create_wine_documents(wine_data)
    if not langchain_documents:
        print("No documents created. Exiting.")
        return

    # 4. Initialize embeddings model
    print(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}...")
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME) # New instantiation
    except Exception as e:
        print(f"Error initializing HuggingFaceEmbeddings: {e}") # Updated error message
        print("Please ensure 'sentence-transformers' and 'langchain-huggingface' and their dependencies are installed correctly.") # Updated help message
        return
        
    # 5. Create FAISS vector store and add documents
    print("Creating FAISS vector store from documents...")
    try:
        # Check if langchain_documents is not empty
        if not langchain_documents:
            print("No documents to add to FAISS store. Exiting.")
            return

        faiss_store = FAISS.from_documents(langchain_documents, embeddings)
        print("FAISS vector store created successfully.")
    except Exception as e:
        print(f"Error creating FAISS vector store: {e}")
        return
        
    # 6. Save FAISS index and documents
    print(f"Saving FAISS index to: {FAISS_INDEX_PATH}...")
    try:
        faiss_store.save_local(FAISS_INDEX_PATH)
        print(f"FAISS index saved successfully to {FAISS_INDEX_PATH}/index.faiss and {FAISS_INDEX_PATH}/index.pkl")
    except Exception as e:
        print(f"Error saving FAISS index: {e}")
        return
        
    print("RAG pipeline indexing process completed.")

# --- Query Pipeline ---
def query_sommelier(question_text):
    """
    Loads the FAISS index and queries the AI Sommelier.
    """
    print(f"Querying AI Sommelier with: '{question_text}'")

    # 1. Load OpenAI API key
    api_key = load_openai_api_key()
    if not api_key:
        print("Error: OPENAI_API_KEY not found. Cannot query the LLM.")
        return

    # 2. Initialize embeddings model (must be the same as used for indexing)
    print(f"Initializing embedding model: {EMBEDDING_MODEL_NAME}...")
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL_NAME)
    except Exception as e:
        print(f"Error initializing HuggingFaceEmbeddings: {e}")
        return

    # 3. Load the FAISS index
    print(f"Loading FAISS index from: {FAISS_INDEX_PATH}...")
    if not os.path.exists(FAISS_INDEX_PATH):
        print(f"Error: FAISS index not found at {FAISS_INDEX_PATH}. Please run the indexing pipeline first.")
        return
    try:
        faiss_store = FAISS.load_local(FAISS_INDEX_PATH, embeddings, allow_dangerous_deserialization=True)
        print("FAISS index loaded successfully.")
    except Exception as e:
        print(f"Error loading FAISS index: {e}")
        return

    # 4. Initialize LLM
    print("Initializing LLM (gpt-4o-mini)...")
    try:
        llm = ChatOpenAI(openai_api_key=api_key, model_name="gpt-4o-mini", temperature=0.3)
    except Exception as e:
        print(f"Error initializing ChatOpenAI: {e}")
        return

    # 5. Create RetrievalQA chain
    # This chain will retrieve documents from the FAISS store and use them to answer the question.
    print("Creating RetrievalQA chain...")
    try:
        # k=5 means it will retrieve the top 5 most similar documents.
        retriever = faiss_store.as_retriever(search_kwargs={"k": 3}) 
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff", # "stuff" puts all retrieved docs into the context.
                               # Other types: "map_reduce", "refine", "map_rerank"
            retriever=retriever,
            return_source_documents=True # Optionally return source documents
        )
        print("RetrievalQA chain created successfully.")
    except Exception as e:
        print(f"Error creating RetrievalQA chain: {e}")
        return

    # 6. Ask the question
    print("\n--- AI Sommelier's Response ---")
    try:
        result = qa_chain.invoke({"query": question_text})
        print("Answer:", result["result"])
        
        print("\n--- Source Documents ---")
        for i, doc in enumerate(result["source_documents"]):
            print(f"Source {i+1} (Name: {doc.metadata.get('name', 'N/A')} - Producer: {doc.metadata.get('brandName', 'N/A')}):")
            # print(doc.page_content) # Uncomment to see full content of source docs
            print("-" * 20)

    except Exception as e:
        print(f"Error during query execution: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG Pipeline for AI Sommelier")
    parser.add_argument("mode", choices=["index", "query"], help="Mode to run: 'index' to build/update the FAISS index, 'query' to ask a question.")
    parser.add_argument("-q", "--question", type=str, help="Question to ask the AI Sommelier (required for 'query' mode).")

    args = parser.parse_args()

    if args.mode == "index":
        run_indexing_pipeline()
    elif args.mode == "query":
        if not args.question:
            parser.error("The --question (-q) argument is required for 'query' mode.")
        query_sommelier(args.question)
