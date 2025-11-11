# ai_backend/services/aws_service.py
"""
AWS S3 Service Handler
Manages all AWS S3 operations for the Room Designer application
"""

import boto3
import os
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class AWSService:
    """
    AWS S3 operations handler
    
    Provides methods for:
    - Bucket management
    - File upload/download
    - File deletion
    - Public access configuration
    """
    
    def __init__(
        self,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        region: str = "us-east-1"
    ):
        """
        Initialize AWS S3 service
        
        Args:
            access_key: AWS access key ID
            secret_key: AWS secret access key
            bucket_name: S3 bucket name
            region: AWS region (default: us-east-1)
        """
        self.bucket_name = bucket_name
        self.region = region
        
        try:
            # Initialize S3 client
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Initialize S3 resource (for higher-level operations)
            self.s3_resource = boto3.resource(
                's3',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            logger.info(f"AWS S3 client initialized for bucket: {bucket_name} (region: {region})")
            
        except Exception as e:
            logger.error(f"Failed to initialize AWS client: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test if AWS credentials are valid and bucket is accessible"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully connected to bucket: {self.bucket_name}")
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                logger.error(f"Bucket '{self.bucket_name}' does not exist")
            elif error_code == '403':
                logger.error(f"Access denied to bucket '{self.bucket_name}'")
            else:
                logger.error(f"Connection error: {e}")
            return False
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False
    
    def bucket_exists(self) -> bool:
        """Check if bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError:
            return False
    
    def create_bucket(self) -> bool:
        """Create S3 bucket if it doesn't exist"""
        try:
            if self.bucket_exists():
                logger.info(f"Bucket already exists: {self.bucket_name}")
                return True
            
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=self.bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )
            
            logger.info(f"Bucket created: {self.bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to create bucket: {e}")
            return False
    
    def set_bucket_policy_public_read(self) -> bool:
        """Set bucket policy to allow public read access"""
        import json
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{self.bucket_name}/*"
                }
            ]
        }
        
        try:
            self.s3_client.put_bucket_policy(
                Bucket=self.bucket_name,
                Policy=json.dumps(policy)
            )
            logger.info("Bucket policy set to public read")
            return True
        except ClientError as e:
            logger.error(f"Failed to set bucket policy: {e}")
            return False
    
    def upload_file(
        self,
        file_path: str,
        object_name: Optional[str] = None,
        make_public: bool = True
    ) -> Optional[str]:
        """Upload file to S3 bucket"""
        if object_name is None:
            object_name = os.path.basename(file_path)
        
        try:
            content_type = 'image/jpeg'
            if file_path.endswith('.png'):
                content_type = 'image/png'
            elif file_path.endswith('.txt'):
                content_type = 'text/plain'
            
            extra_args = {'ContentType': content_type}
            if make_public:
                extra_args['ACL'] = 'public-read'
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                object_name,
                ExtraArgs=extra_args
            )
            
            url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{object_name}"
            logger.info(f"File uploaded: {url}")
            return url
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            return None
        except NoCredentialsError:
            logger.error("AWS credentials not available")
            return None
        except ClientError as e:
            logger.error(f"Upload failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            return None
    
    def delete_file(self, object_name: str) -> bool:
        """Delete file from S3 bucket"""
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            logger.info(f"File deleted: {object_name}")
            return True
        except ClientError as e:
            logger.error(f"Delete failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during deletion: {e}")
            return False
    
    def list_files(self, prefix: str = "", max_keys: int = 1000) -> List[str]:
        """List files in bucket with optional prefix filter"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
                logger.info(f"Listed {len(files)} files with prefix '{prefix}'")
                return files
            else:
                logger.info(f"No files found with prefix '{prefix}'")
                return []
        except ClientError as e:
            logger.error(f"List failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during listing: {e}")
            return []
    
    def download_file(self, object_name: str, local_path: str) -> bool:
        """Download file from S3 to local path"""
        try:
            self.s3_client.download_file(
                self.bucket_name,
                object_name,
                local_path
            )
            logger.info(f"File downloaded: {object_name} -> {local_path}")
            return True
        except ClientError as e:
            logger.error(f"Download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return False
    
    def get_file_url(self, object_name: str) -> str:
        """Get public URL for an object"""
        return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{object_name}"
    
    def file_exists(self, object_name: str) -> bool:
        """Check if file exists in bucket"""
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            return True
        except ClientError:
            return False
    
    def get_file_size(self, object_name: str) -> Optional[int]:
        """Get file size in bytes"""
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_name
            )
            return response['ContentLength']
        except ClientError:
            return None
    
    def copy_file(self, source_key: str, dest_key: str) -> bool:
        """Copy file within the same bucket"""
        try:
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_key
            }
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key
            )
            logger.info(f"File copied: {source_key} -> {dest_key}")
            return True
        except ClientError as e:
            logger.error(f"Copy failed: {e}")
            return False
    
    def delete_folder(self, prefix: str) -> bool:
        """Delete all files with given prefix (simulates folder deletion)"""
        try:
            objects = self.list_files(prefix=prefix)
            if not objects:
                logger.info(f"No files to delete with prefix '{prefix}'")
                return True
            
            for i in range(0, len(objects), 1000):
                batch = objects[i:i+1000]
                delete_dict = {
                    'Objects': [{'Key': key} for key in batch],
                    'Quiet': True
                }
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete=delete_dict
                )
            
            logger.info(f"Deleted {len(objects)} files with prefix '{prefix}'")
            return True
        except ClientError as e:
            logger.error(f"Folder deletion failed: {e}")
            return False
    
    def get_bucket_size(self) -> dict:
        """Get bucket statistics (file count and total size)"""
        try:
            total_size = 0
            file_count = 0
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name)
            
            for page in pages:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        total_size += obj['Size']
                        file_count += 1
            
            return {
                'count': file_count,
                'size_bytes': total_size,
                'size_mb': round(total_size / (1024 * 1024), 2),
                'size_gb': round(total_size / (1024 * 1024 * 1024), 2)
            }
        except ClientError as e:
            logger.error(f"Failed to get bucket size: {e}")
            return {'count': 0, 'size_bytes': 0, 'size_mb': 0, 'size_gb': 0}


# Global instance
_aws_service_instance: Optional[AWSService] = None


def init_aws_service(
    access_key: str, 
    secret_key: str, 
    bucket: str, 
    region: str
) -> AWSService:
    """Initialize global AWS service instance"""
    global _aws_service_instance
    _aws_service_instance = AWSService(access_key, secret_key, bucket, region)
    return _aws_service_instance


def get_aws_service() -> AWSService:
    """Get global AWS service instance"""
    if _aws_service_instance is None:
        raise RuntimeError("AWS service not initialized. Call init_aws_service() first.")
    return _aws_service_instance


def reset_aws_service():
    """Reset global AWS service instance (for testing)"""
    global _aws_service_instance
    _aws_service_instance = None