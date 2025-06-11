import asyncio
import argparse
import sys
import os

# Add the parent directory (backend) to sys.path to allow absolute imports
# This is necessary if you run this script directly from the 'rag' directory
# or if the 'app' module is not automatically found.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from app.rag.rag_pipeline import RAGPipeline
    from app.database import SessionLocal, engine, Base # To create tables if they don\'t exist
    from app.models import Wine # Ensure Wine model is imported for table creation
    from app.config import settings # For OPENAI_API_KEY
    from app.rag.config import FAISS_INDEX_PATH, EMBEDDING_MODEL_NAME, LLM_MODEL_NAME # For defaults
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Please ensure that the script is run from the \'backend\' directory or that PYTHONPATH is set correctly.")
    print("Alternatively, ensure all necessary __init__.py files are in place to make \'app\' a package.")
    sys.exit(1)

async def main():
    """
    Main function to initialize database (if needed) and run the RAG indexing pipeline.
    """
    print("Initializing database and RAG pipeline...")

    # Initialize database tables (optional, but good for first run)
    # This ensures that the 'wines' table exists before trying to read from it.
    # In a production setup, migrations (e.g., with Alembic) would handle this.
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Uncomment to drop tables first
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables checked/created.")

    parser = argparse.ArgumentParser(description="Create or update the FAISS vector index for the AI Sommelier.")
    # No arguments needed for now, as it only does one thing: indexing.
    # Potentially add --force-reindex or other options later.
    args = parser.parse_args()

    print("Instantiating RAGPipeline...")
    # Pass configuration to RAGPipeline constructor
    pipeline = RAGPipeline(
        openai_api_key=settings.OPENAI_API_KEY,
        faiss_index_path=FAISS_INDEX_PATH,
        embedding_model_name=EMBEDDING_MODEL_NAME,
        llm_name=LLM_MODEL_NAME
    )
    
    print("Running indexing process...")
    await pipeline.run_indexing()
    print("Indexing process has been initiated and should complete shortly.")

if __name__ == "__main__":
    # Ensure the script is run from the 'backend' directory for consistent pathing
    # or adjust paths in config.py accordingly.
    # Example: python -m app.rag.create_index
    # or from backend dir: python app/rag/create_index.py
    
    # Check if running from backend directory
    if not os.getcwd().endswith("\'backend\'"):
        print("Warning: This script is ideally run from the \'backend\' directory.")
        print(f"Current directory: {os.getcwd()}")
        # You might want to change directory or adjust sys.path more robustly
        # For now, we assume config.py paths are absolute or correctly relative

    asyncio.run(main())
