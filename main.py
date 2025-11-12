# from fastapi import FastAPI
# from dotenv import load_dotenv
# from ai_backend.api import room, furniture, generation

# load_dotenv()

# app = FastAPI(title="Room Designer API")

# app.include_router(room.router, prefix="/room", tags=["room"])
# app.include_router(furniture.router, prefix="/furniture", tags=["furniture"])
# app.include_router(generation.router, prefix="/generation", tags=["generation"])

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)



# main.py
"""
Room Designer API - Complete FastAPI Application
All endpoints are included via routers
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import logging

# Load environment variables first
load_dotenv()

# Import routers (these contain all the endpoints)
from ai_backend.api import room, furniture, generation
from ai_backend.services.aws_service import init_aws_service

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Room Designer API",
    description="AI-powered interior design with furniture placement and theme selection",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware (for frontend integration)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: ["https://yourdomain.com"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services when app starts"""
    logger.info("🚀 Starting Room Designer API...")
    
    try:
        # Initialize AWS S3 service
        init_aws_service(
            access_key=os.getenv("AWS_ACCESS_KEY_ID"),
            secret_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            bucket=os.getenv("AWS_S3_BUCKET"),
            region=os.getenv("AWS_REGION", "eu-north-1")
        )
        logger.info("✅ AWS S3 service initialized")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize AWS: {e}")
        logger.warning("⚠️  App will run but image uploads may fail")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup when app shuts down"""
    logger.info("🛑 Shutting down Room Designer API...")


# =====================================================
# INCLUDE ALL ROUTERS (This adds all endpoints)
# =====================================================

# Room dimension endpoints (/room/*)
app.include_router(
    room.router, 
    prefix="/room", 
    tags=["Room Dimensions"]
)

# Furniture search endpoints (/furniture/*)
app.include_router(
    furniture.router, 
    prefix="/furniture", 
    tags=["Furniture Search"]
)

# Image generation endpoints (/generation/*)
app.include_router(
    generation.router, 
    prefix="/generation", 
    tags=["Image Generation"]
)


# =====================================================
# ROOT ENDPOINTS (Health checks)
# =====================================================

@app.get("/", tags=["Root"])
def root():
    """
    Root endpoint - API status check
    
    Returns:
        API status and available endpoints
    """
    return {
        "status": "online",
        "message": "Room Designer API is running!",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "room_dimensions": {
                "set": "POST /room/dimensions",
                "fit_check": "POST /room/fit-check"
            },
            "furniture": {
                "search": "POST /furniture/search"
            },
            "generation": {
                "generate": "POST /generation/generate"
            }
        }
    }


@app.get("/health", tags=["Root"])
def health_check():
    """
    Health check endpoint
    
    Returns:
        Service status information
    """
    return {
        "status": "healthy",
        "services": {
            "api": "running",
            "aws_s3": "configured" if os.getenv("AWS_S3_BUCKET") else "not configured",
            "replicate_ai": "configured" if os.getenv("REPLICATE_API_TOKEN") else "not configured"
        },
        "environment": {
            "aws_region": os.getenv("AWS_REGION", "not set"),
            "aws_bucket": os.getenv("AWS_S3_BUCKET", "not set")
        }
    }


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":
    import uvicorn
    
    # Run with auto-reload for development
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )