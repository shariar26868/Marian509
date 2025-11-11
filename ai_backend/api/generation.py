# ai_backend/api/generation.py - FULL REPLACE

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from ai_backend.services.ai_generator import generate_room_image
from ai_backend.services.storage import upload_to_s3
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/generate")
async def generate_image(
    room_image: UploadFile = File(...),
    prompt: str = Form(...),
    theme: str = Form(...),
    furniture_links: str = Form(...)  # Comma-separated links
):
    """
    Generate interior design image
    
    Args:
        room_image: Room photo (JPEG/PNG)
        prompt: Placement instructions (e.g., "sofa on left wall")
        theme: Design theme
        furniture_links: Comma-separated furniture URLs
    
    Returns:
        Generated image URL from S3
    """
    
    try:
        # Validate image file
        if not room_image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Please upload an image (JPEG/PNG)"
            )
        
        # Read image bytes
        logger.info(f"Reading room image: {room_image.filename}")
        image_bytes = await room_image.read()
        
        # Check file size (max 10MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=400, 
                detail="Image too large. Maximum size is 10MB"
            )
        
        # Split furniture links
        links = [link.strip() for link in furniture_links.split(",") if link.strip()]
        
        if not links:
            raise HTTPException(
                status_code=400, 
                detail="Please provide at least one furniture link"
            )
        
        logger.info(f"Generating image with theme: {theme}, furniture count: {len(links)}")
        
        # Generate image using Replicate
        generated_image_path = generate_room_image(
            image_bytes, 
            prompt, 
            theme, 
            links
        )
        
        logger.info("Image generation complete, uploading to S3...")
        
        # Upload to S3
        s3_url = upload_to_s3(generated_image_path, folder="generated")
        
        logger.info(f"✅ Image uploaded: {s3_url}")
        
        return {
            "success": True,
            "generated_image_url": s3_url,
            "message": "Image generated successfully",
            "furniture_count": len(links)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Generation endpoint error: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Image generation failed: {str(e)}"
        )