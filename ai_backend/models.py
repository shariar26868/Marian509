# ai_backend/models.py
from pydantic import BaseModel
from typing import List, Optional

class RoomDimensions(BaseModel):
    length: float
    width: float
    height: Optional[float] = None

class FurnitureSelection(BaseModel):
    type: str
    subtype: str
    width: float
    depth: float
    height: Optional[float] = None

class PriceRange(BaseModel):
    min: float
    max: float

class FurnitureItem(BaseModel):
    name: str
    link: str
    price: float
    image_url: str
    dimensions: dict  # e.g., {"width": 36, "depth": 36, "height": 34}

class GenerationRequest(BaseModel):
    room_image: bytes  # Or path
    prompt: str
    theme: str
    furniture_links: List[str]