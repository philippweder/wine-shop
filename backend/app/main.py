from fastapi import FastAPI, Depends, HTTPException  # Added HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
from typing import List

from app import models # No alias needed for models
# Import wine-specific schemas from the new file
from app.wine_app_schemas import Wine, WineCreate, WineUpdate

from app.database import engine, get_db  # Changed to absolute import from app

# Add this import for CORS
from fastapi.middleware.cors import CORSMiddleware

# Import and include the RAG API router
from app.api.endpoints import rag as rag_router # Corrected import alias


# Create tables on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    yield


app = FastAPI(
    title="Sentio API",
    description="API for Sentio, the online wine shop.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS Middleware Configuration
# Origins that are allowed to make requests to this FastAPI server.
# Using \"*\" allows all origins, which is fine for development but
# you might want to restrict this in production.
origins = [
    "http://localhost:3000",  # Next.js frontend
    "http://127.0.0.1:3000", # Also for Next.js frontend
    # Add any other origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows specific origins
    allow_credentials=True, # Allows cookies to be included in requests
    allow_methods=["*"],    # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],    # Allows all headers
)


@app.get("/")
async def root():
    return {"message": "Welcome to the Wine Shop API"}


# Example: Get all wines
@app.get("/wines/", response_model=list[Wine]) # Use aliased schema
async def read_wines(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Wine).offset(skip).limit(limit))
    wines = result.scalars().all()
    return wines


# Example: Create a new wine
@app.post("/wines/", response_model=Wine, status_code=201) # Use aliased schema
async def create_wine(wine: WineCreate, db: AsyncSession = Depends(get_db)): # Use app_schemas
    db_wine = models.Wine(**wine.model_dump())  # Use model_dump() for Pydantic V2
    db.add(db_wine)
    await db.commit()
    await db.refresh(db_wine)
    return db_wine


# Add other CRUD operations for wines (get by ID, update, delete)
# and for other models as you define them.

@app.get("/wines/{wine_id}", response_model=Wine) # Use aliased schema
async def read_wine(wine_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Wine).filter(models.Wine.id == wine_id))
    db_wine = result.scalars().first()
    if db_wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return db_wine

@app.put("/wines/{wine_id}", response_model=Wine) # Use aliased schema
async def update_wine(wine_id: int, wine: WineUpdate, db: AsyncSession = Depends(get_db)): # Use app_schemas
    result = await db.execute(select(models.Wine).filter(models.Wine.id == wine_id))
    db_wine = result.scalars().first()
    if db_wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")

    update_data = wine.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_wine, key, value)

    await db.commit()
    await db.refresh(db_wine)
    return db_wine

@app.delete("/wines/{wine_id}", response_model=Wine) # Use aliased schema
async def delete_wine(wine_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Wine).filter(models.Wine.id == wine_id))
    db_wine = result.scalars().first()
    if db_wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")

    await db.delete(db_wine)
    await db.commit()
    return db_wine

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Create all database tables if they don't exist
# This is useful for development but consider Alembic for production migrations
async def create_tables():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Optional: drop tables first
        await conn.run_sync(models.Base.metadata.create_all)


@app.on_event("startup")
async def startup_event():
    print("Application startup: Creating database tables if they don't exist...")
    await create_tables()
    print("Database tables checked/created.")
    # You could also pre-load the RAG pipeline's vector store here if desired
    # from app.api.endpoints.rag import rag_pipeline_instance
    # if not rag_pipeline_instance.vector_store:
    #     print("Pre-loading FAISS index at startup...")
    #     rag_pipeline_instance.load_vector_store()
    #     if rag_pipeline_instance.vector_store:
    #         print("FAISS index pre-loaded.")
    #     else:
    #         print("Warning: FAISS index could not be pre-loaded at startup.")


# Include the new RAG router
app.include_router(rag_router.router, prefix="/api/ai-sommelier", tags=["AI Sommelier"])


@app.get("/ping", summary="Health check")
async def ping():
    return {"message": "pong"}
