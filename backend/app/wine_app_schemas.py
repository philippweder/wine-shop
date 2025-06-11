from pydantic import BaseModel, ConfigDict
from typing import Optional

class WineBase(BaseModel):
    name: str
    type: Optional[str] = None # Made optional as some entries might miss it
    varietal: Optional[str] = None # Made optional
    price: float
    vintage: Optional[int] = None
    region: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    producer: Optional[str] = None # New field (brandName from JSON)
    sub_region: Optional[str] = None # New field
    food_pairing: Optional[str] = None # New field
    drinking_window: Optional[str] = None # New field
    body_type: Optional[str] = None # New field
    product_url: Optional[str] = None # New field
    size: Optional[str] = None # New field
    source: Optional[str] = None # New field

class WineCreate(WineBase):
    pass

class WineUpdate(WineBase):
    name: Optional[str] = None
    type: Optional[str] = None
    varietal: Optional[str] = None
    price: Optional[float] = None
    vintage: Optional[int] = None
    region: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    producer: Optional[str] = None
    sub_region: Optional[str] = None
    food_pairing: Optional[str] = None
    drinking_window: Optional[str] = None
    body_type: Optional[str] = None
    product_url: Optional[str] = None
    size: Optional[str] = None
    source: Optional[str] = None

class Wine(WineBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
