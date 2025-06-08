from fastapi import FastAPI, Depends, HTTPException  # Added HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from contextlib import asynccontextmanager
from typing import List

from app import models, schemas  # Changed to absolute import from app
from app.database import engine, get_db  # Changed to absolute import from app

# Add this import for CORS
from fastapi.middleware.cors import CORSMiddleware

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
@app.get("/wines/", response_model=list[schemas.Wine])
async def read_wines(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(models.Wine).offset(skip).limit(limit))
    wines = result.scalars().all()
    return wines


# Example: Create a new wine
@app.post("/wines/", response_model=schemas.Wine, status_code=201)
async def create_wine(wine: schemas.WineCreate, db: AsyncSession = Depends(get_db)):
    db_wine = models.Wine(**wine.model_dump())  # Use model_dump() for Pydantic V2
    db.add(db_wine)
    await db.commit()
    await db.refresh(db_wine)
    return db_wine


# Add other CRUD operations for wines (get by ID, update, delete)
# and for other models as you define them.

@app.get("/wines/{wine_id}", response_model=schemas.Wine)
async def read_wine(wine_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Wine).filter(models.Wine.id == wine_id))
    db_wine = result.scalars().first()
    if db_wine is None:
        raise HTTPException(status_code=404, detail="Wine not found")
    return db_wine

@app.put("/wines/{wine_id}", response_model=schemas.Wine)
async def update_wine(wine_id: int, wine: schemas.WineUpdate, db: AsyncSession = Depends(get_db)):
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

@app.delete("/wines/{wine_id}", response_model=schemas.Wine)
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
