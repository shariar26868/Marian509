# ai_backend/api/furniture.py - FULL REPLACE

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ai_backend.models import FurnitureItem, PriceRange
from ai_backend.services.furniture import search_furniture
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class FurnitureRequest(BaseModel):
    theme: str
    room_type: str
    furniture_types: list[str]  # e.g., ["Sofa", "Coffee Table"]
    price_range: PriceRange


@router.post("/search")
async def search_furnitures(request: FurnitureRequest):
    """
    Search furniture from theme websites
    
    Args:
        request: Furniture search parameters
    
    Returns:
        List of furniture items with links and prices
    """
    
    try:
        # Validate theme
        from ai_backend.config import THEMES
        if request.theme.upper() not in THEMES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid theme. Valid themes: {', '.join(THEMES.keys())}"
            )
        
        logger.info(f"Searching furniture: theme={request.theme}, types={request.furniture_types}")
        
        # Search furniture
        results = search_furniture(
            request.theme, 
            request.room_type, 
            request.furniture_types, 
            request.price_range
        )
        
        if not results:
            return {
                "success": True,
                "results": [],
                "message": "No furniture found. Try adjusting your price range or theme.",
                "count": 0
            }
        
        logger.info(f"Found {len(results)} furniture items")
        
        return {
            "success": True,
            "results": results,
            "message": f"Found {len(results)} items",
            "count": len(results)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Furniture search error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Furniture search failed: {str(e)}"
        )