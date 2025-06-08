from pydantic import BaseModel, ConfigDict
from typing import Optional

class WineBase(BaseModel):
    name: str
    type: str
    varietal: str
    price: float
    vintage: Optional[int] = None
    region: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

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

class Wine(WineBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
