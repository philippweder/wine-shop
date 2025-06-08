from sqlalchemy import Column, Integer, String, Float, Text
from app.database import Base # Changed to absolute import

class Wine(Base):
    __tablename__ = "wines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String) # e.g., Red, White, Rosé, Sparkling, Dessert
    varietal = Column(String) # e.g., Cabernet Sauvignon, Chardonnay, Pinot Noir
    vintage = Column(Integer, nullable=True)
    region = Column(String, nullable=True)
    country = Column(String, nullable=True)
    price = Column(Float)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    # Add more fields as needed, e.g., alcohol_content, producer, tasting_notes, stock_quantity
