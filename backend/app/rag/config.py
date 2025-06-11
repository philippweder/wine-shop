\
import os

# --- Paths ---
# Assuming the script is run from the 'backend' directory or its path is adjusted accordingly
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) # Points to backend/
APP_DIR = os.path.join(BACKEND_DIR, "app") # Points to backend/app/

# Path to the .env file in the backend directory
DOTENV_PATH = os.path.join(BACKEND_DIR, ".env")

# Path for wine data - assuming it will be moved here
# Alternatively, this could be an absolute path or an environment variable
DATA_DIR = os.path.join(APP_DIR, "data")

# Path for FAISS index within the RAG module
RAG_DIR = os.path.join(APP_DIR, "rag")
FAISS_INDEX_NAME = "faiss_index_backend" # New name to avoid conflict with lab index
FAISS_INDEX_PATH = os.path.join(RAG_DIR, FAISS_INDEX_NAME)

# --- Model Configuration ---
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
LLM_MODEL_NAME = "gpt-4o-mini"
LLM_TEMPERATURE = 0.3
RETRIEVER_K = 10 # Number of documents to retrieve (increased from 5 for debugging)

# --- Data Fields ---
# Fields to include in the document for embedding
IMPORTANT_FIELDS = [
    "name", "brandName", "varietal", "description", "food_pairing",
    "region", "sub_region", "type", "year", "alcohol_content", "price",
    "country", "aroma", "taste", "winemaking", "awards",
    "serving_temperature", "storage_potential"
]
