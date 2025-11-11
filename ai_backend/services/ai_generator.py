# ai_backend/services/ai_generator.py - FULL REPLACE

import replicate
import os
import tempfile
import requests
import logging

logger = logging.getLogger(__name__)

os.environ["REPLICATE_API_TOKEN"] = os.getenv("REPLICATE_API_TOKEN")


def generate_room_image(
    room_image_bytes: bytes, 
    prompt: str, 
    theme: str, 
    furniture_links: list[str]
) -> str:
    """
    Generate room image using Replicate Stable Diffusion
    
    Args:
        room_image_bytes: Original room photo bytes
        prompt: User placement instructions
        theme: Design theme
        furniture_links: List of furniture URLs
    
    Returns:
        Path to generated image file
    """
    
    # Save room image to temp file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_room:
        temp_room.write(room_image_bytes)
        room_image_path = temp_room.name
    
    logger.info(f"Room image saved to: {room_image_path}")
    
    try:
        # Prepare prompt
        full_prompt = f"""
        Professional interior design photo, {theme} style room.
        {prompt}
        High quality, realistic lighting, 4k resolution, photorealistic.
        Furniture placement: {', '.join([link.split('/')[-1] for link in furniture_links[:3]])}
        """
        
        negative_prompt = "blurry, distorted, cartoon, unrealistic, low quality, bad lighting"
        
        logger.info(f"Generating image with prompt: {full_prompt[:100]}...")
        
        # Use SDXL with img2img
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "image": open(room_image_path, "rb"),
                "prompt": full_prompt,
                "negative_prompt": negative_prompt,
                "num_inference_steps": 30,
                "guidance_scale": 7.5,
                "strength": 0.6,  # Keep 40% of original image
                "num_outputs": 1
            }
        )
        
        # Output is a list of URLs
        output_url = output[0] if isinstance(output, list) else output
        
        logger.info(f"Image generated: {output_url}")
        
        # Download generated image
        response = requests.get(output_url, timeout=60)
        response.raise_for_status()
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_gen:
            temp_gen.write(response.content)
            generated_path = temp_gen.name
        
        # Cleanup original room image
        try:
            os.remove(room_image_path)
        except:
            pass
        
        logger.info(f"Generated image saved: {generated_path}")
        return generated_path
        
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        # Cleanup
        try:
            os.remove(room_image_path)
        except:
            pass
        raise Exception(f"Failed to generate image: {str(e)}")