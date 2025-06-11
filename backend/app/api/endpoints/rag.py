\
# filepath: /Users/weder/Documents/side_projects/wine-shop/backend/app/api/endpoints/rag.py
from fastapi import APIRouter, Depends, HTTPException
from app.rag.rag_pipeline import RAGPipeline
from app.schemas.rag_schemas import SommelierQueryRequest, SommelierQueryResponse
from app.config import settings # Import the settings instance directly
from app.rag.config import FAISS_INDEX_PATH, EMBEDDING_MODEL_NAME, LLM_MODEL_NAME

router = APIRouter()

# Global variable to hold the RAG pipeline instance
# This is a simple way to cache the pipeline. For production, consider more robust caching.
rag_pipeline_instance: RAGPipeline | None = None

async def get_rag_pipeline() -> RAGPipeline:
    """
    Dependency to get a RAGPipeline instance.
    Initializes the pipeline if it hasn't been already.
    """
    global rag_pipeline_instance
    if rag_pipeline_instance is None:
        if not settings.OPENAI_API_KEY:
            raise HTTPException(status_code=500, detail="OpenAI API key not configured.")
        
        try:
            rag_pipeline_instance = RAGPipeline(
                faiss_index_path=FAISS_INDEX_PATH,
                embedding_model_name=EMBEDDING_MODEL_NAME,
                llm_name=LLM_MODEL_NAME,
                openai_api_key=settings.OPENAI_API_KEY
            )
            # Correctly load vector store and initialize QA chain
            if not rag_pipeline_instance.load_vector_store():
                # Error messages are printed within load_vector_store
                raise HTTPException(status_code=500, detail=f"Failed to load FAISS index from {FAISS_INDEX_PATH}. Please run indexing.")
            if not rag_pipeline_instance._initialize_qa_chain():
                # Error messages are printed within _initialize_qa_chain
                raise HTTPException(status_code=500, detail="Failed to initialize QA chain.")
            print(f"RAG Pipeline initialized and QA chain ready with index: {FAISS_INDEX_PATH}")
        except FileNotFoundError: # This might be redundant if load_vector_store handles it
            raise HTTPException(status_code=500, detail=f"FAISS index not found at {FAISS_INDEX_PATH}. Please run indexing.")
        except Exception as e:
            print(f"Error initializing RAG pipeline: {e}")
            raise HTTPException(status_code=500, detail=f"Could not initialize RAG pipeline: {e}")
            
    # This check might be redundant if the above initialization is robust
    # or could be a safety net if the instance exists but chain is somehow None
    if not rag_pipeline_instance.qa_chain:
        try:
            if not rag_pipeline_instance.load_vector_store(): # Ensure vector store is loaded first
                 raise HTTPException(status_code=500, detail="Failed to load vector store for QA chain re-initialization.")
            if not rag_pipeline_instance._initialize_qa_chain():
                raise HTTPException(status_code=500, detail="Could not re-initialize RAG QA chain.")
            print("RAG QA chain re-initialized successfully.")
        except Exception as e:
            print(f"Error re-initializing QA chain: {e}")
            raise HTTPException(status_code=500, detail=f"Could not re-initialize RAG QA chain: {e}")
            
    return rag_pipeline_instance

@router.post("/query", response_model=SommelierQueryResponse)
async def query_sommelier(
    request: SommelierQueryRequest,
    pipeline: RAGPipeline = Depends(get_rag_pipeline)
):
    """
    Accepts a user query and returns the AI Sommelier's response along with source documents.
    """
    if not request.question:  # Changed from request.query
        raise HTTPException(status_code=400, detail="Query cannot be empty.")
    
    try:
        print(f"Received query: {request.question}")  # Changed from request.query
        # The RAGPipeline's query method now returns a dict
        response_data = await pipeline.query(request.question) # Changed from request.query # Changed to await
        
        if "error" in response_data:
            raise HTTPException(status_code=500, detail=response_data["error"])

        # Ensure source_docs are serializable; they should be dicts from RAGPipeline
        # The RAGPipeline.query method should already return them in the correct format.
        return SommelierQueryResponse(answer=response_data.get("answer"), sources=response_data.get("source_documents", []))
    except Exception as e:
        print(f"Error during RAG query processing: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {e}")

# To include this router in your main application:
# from app.api.endpoints import rag as rag_router
# app.include_router(rag_router.router, prefix="/api/ai-sommelier", tags=["AI Sommelier"])

