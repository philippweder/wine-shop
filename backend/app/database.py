from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings  # Changed to absolute import

DATABASE_URL = settings.DATABASE_URL # Corrected attribute name to uppercase

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, class_=AsyncSession
)
Base = declarative_base()

async def get_db():
    async with SessionLocal() as session:
        yield session
