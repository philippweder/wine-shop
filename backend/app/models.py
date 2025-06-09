from sqlalchemy import Column, Integer, String, Float, Text
from app.database import Base # Changed to absolute import

class Wine(Base):
    __tablename__ = "wines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    type = Column(String) # e.g., Red, White, Rosé, Sparkling, Dessert
    varietal = Column(String, nullable=True) # Made nullable as some entries might miss it
    vintage = Column(Integer, nullable=True)
    region = Column(String, nullable=True)
    country = Column(String, nullable=True)
    price = Column(Float)
    description = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    producer = Column(String, nullable=True) # New field
    sub_region = Column(String, nullable=True) # New field
    food_pairing = Column(Text, nullable=True) # New field
    drinking_window = Column(String, nullable=True) # New field
    body_type = Column(String, nullable=True) # New field
    product_url = Column(String, nullable=True) # New field
    size = Column(String, nullable=True) # New field
    source = Column(String, nullable=True) # New field to store "martel.ch"
    # Add more fields as needed, e.g., alcohol_content, tasting_notes, stock_quantity
