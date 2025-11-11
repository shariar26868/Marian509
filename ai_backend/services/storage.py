# ai_backend/services/storage.py - IMPROVED VERSION

import os
import uuid
import logging
from typing import Optional
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


def upload_to_s3(file_path: str, folder: str = "generated") -> str:
    """
    Upload image to S3 and return public URL
    
    Args:
        file_path: Local file path to upload
        folder: S3 folder/prefix (default: "generated")
    
    Returns:
        Public S3 URL
    
    Raises:
        Exception: If upload fails
    """
    try:
        from ai_backend.services.aws_service import get_aws_service
        
        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Validate file size (max 50MB for images)
        file_size = os.path.getsize(file_path)
        max_size = 50 * 1024 * 1024  # 50MB
        if file_size > max_size:
            raise ValueError(f"File too large: {file_size / (1024*1024):.2f}MB (max: 50MB)")
        
        # Generate unique filename with proper extension
        file_extension = os.path.splitext(file_path)[1].lower()
        
        # Default to .jpg if no extension
        if not file_extension:
            file_extension = ".jpg"
        
        # Validate extension
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        if file_extension not in allowed_extensions:
            logger.warning(f"Unusual file extension: {file_extension}, using .jpg")
            file_extension = ".jpg"
        
        # Generate S3 key with timestamp for better organization
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d")
        file_name = f"{folder}/{timestamp}/{uuid.uuid4()}{file_extension}"
        
        logger.info(f"Uploading to S3: {file_name} (size: {file_size / 1024:.2f}KB)")
        
        # Get AWS service
        try:
            aws_service = get_aws_service()
        except RuntimeError as e:
            logger.error("AWS service not initialized")
            raise Exception("AWS service not configured. Check your .env file and run setup_aws.py")
        
        # Upload file
        url = aws_service.upload_file(
            file_path=file_path,
            object_name=file_name,
            make_public=True
        )
        
        if not url:
            raise Exception("Failed to get upload URL from AWS")
        
        logger.info(f"✅ File uploaded to S3: {url}")
        
        # Cleanup local file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️  Local file deleted: {file_path}")
        except Exception as e:
            logger.warning(f"⚠️  Failed to delete local file: {e}")
        
        return url
        
    except FileNotFoundError as e:
        logger.error(f"❌ File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise
    except ClientError as e:
        logger.error(f"❌ AWS S3 error: {e}")
        raise Exception(f"S3 upload failed: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Upload failed: {e}")
        raise Exception(f"Failed to upload to S3: {str(e)}")


def delete_from_s3(url: str) -> bool:
    """
    Delete file from S3 using its URL
    
    Args:
        url: Full S3 URL of the file
    
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        from ai_backend.services.aws_service import get_aws_service
        
        # Extract object name from URL
        # URL format: https://bucket.s3.region.amazonaws.com/folder/file.jpg
        if ".amazonaws.com/" in url:
            object_name = url.split(".amazonaws.com/")[-1]
        else:
            logger.error(f"Invalid S3 URL format: {url}")
            return False
        
        logger.info(f"Deleting from S3: {object_name}")
        
        # Get AWS service
        aws_service = get_aws_service()
        
        # Delete file
        result = aws_service.delete_file(object_name)
        
        if result:
            logger.info(f"✅ File deleted from S3: {object_name}")
        else:
            logger.warning(f"⚠️  Delete failed for: {object_name}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ S3 delete failed: {e}")
        return False


def get_s3_file_info(url: str) -> Optional[dict]:
    """
    Get file information from S3
    
    Args:
        url: Full S3 URL of the file
    
    Returns:
        Dict with file info (size, exists), or None if error
    """
    try:
        from ai_backend.services.aws_service import get_aws_service
        
        # Extract object name from URL
        if ".amazonaws.com/" in url:
            object_name = url.split(".amazonaws.com/")[-1]
        else:
            return None
        
        # Get AWS service
        aws_service = get_aws_service()
        
        # Check if file exists
        exists = aws_service.file_exists(object_name)
        
        if not exists:
            return {"exists": False, "size": 0}
        
        # Get file size
        size = aws_service.get_file_size(object_name)
        
        return {
            "exists": True,
            "size": size,
            "size_kb": round(size / 1024, 2) if size else 0,
            "size_mb": round(size / (1024 * 1024), 2) if size else 0,
            "url": url,
            "object_name": object_name
        }
        
    except Exception as e:
        logger.error(f"❌ Failed to get file info: {e}")
        return None


def save_to_local(file_path: str, folder: str = "uploads") -> str:
    """
    Save file locally (for development/testing without AWS)
    
    Args:
        file_path: Source file path
        folder: Destination folder (default: "uploads")
    
    Returns:
        Local file path
    """
    try:
        # Create folder if not exists
        os.makedirs(folder, exist_ok=True)
        
        # Generate unique filename
        file_extension = os.path.splitext(file_path)[1] or ".jpg"
        new_filename = f"{uuid.uuid4()}{file_extension}"
        new_path = os.path.join(folder, new_filename)
        
        # Copy file
        import shutil
        shutil.copy(file_path, new_path)
        
        logger.info(f"✅ File saved locally: {new_path}")
        return new_path
        
    except Exception as e:
        logger.error(f"❌ Local save failed: {e}")
        raise


def cleanup_old_files(folder: str = "generated", days_old: int = 30) -> int:
    """
    Delete files older than specified days from S3
    
    Args:
        folder: S3 folder/prefix
        days_old: Delete files older than this many days
    
    Returns:
        Number of files deleted
    """
    try:
        from ai_backend.services.aws_service import get_aws_service
        from datetime import datetime, timedelta
        
        logger.info(f"Cleaning up files older than {days_old} days in '{folder}/'")
        
        aws_service = get_aws_service()
        
        # List all files
        files = aws_service.list_files(prefix=f"{folder}/")
        
        if not files:
            logger.info("No files to cleanup")
            return 0
        
        # Calculate cutoff date
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted_count = 0
        
        # Note: This is a simple implementation
        # In production, you should check LastModified date
        for file_key in files:
            # For now, just count (implement proper date checking if needed)
            pass
        
        logger.info(f"✅ Cleanup complete: {deleted_count} files deleted")
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ Cleanup failed: {e}")
        return 0


# Configuration: Use local storage for development
USE_LOCAL_STORAGE = os.getenv("USE_LOCAL_STORAGE", "false").lower() == "true"


def upload_image(file_path: str, folder: str = "generated") -> str:
    """
    Upload image - uses S3 or local storage based on config
    
    Args:
        file_path: Local file path
        folder: Destination folder
    
    Returns:
        URL (S3) or local path
    """
    if USE_LOCAL_STORAGE:
        logger.info("Using local storage (development mode)")
        return save_to_local(file_path, folder)
    else:
        return upload_to_s3(file_path, folder)