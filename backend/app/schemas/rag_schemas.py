\
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SommelierQueryRequest(BaseModel):
    question: str

class SourceDocument(BaseModel):
    name: Optional[str] = None
    brandName: Optional[str] = None
    page_content_preview: Optional[str] = None
    # You can add other metadata fields you expect from RAGPipeline.query here
    # e.g., source_db_id: Optional[int] = None
    # For now, keeping it aligned with what RAGPipeline.query currently structures
    metadata: Optional[Dict[str, Any]] = None # Or more specific if you refine metadata in pipeline

class SommelierQueryResponse(BaseModel):
    answer: Optional[str] = None
    source_documents: Optional[List[SourceDocument]] = None
    error: Optional[str] = None
