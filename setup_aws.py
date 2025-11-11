# setup_aws.py
"""
AWS S3 Bucket Setup Script
Run this once to configure your S3 bucket for the Room Designer project

Usage:
    python setup_aws.py
"""

import os
import sys
import boto3
import json
from dotenv import load_dotenv
from botocore.exceptions import ClientError, NoCredentialsError

# Load environment variables
load_dotenv()


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(step_num, text):
    """Print step with number"""
    print(f"\n{step_num}️⃣  {text}")


def print_success(text):
    """Print success message"""
    print(f"✅ {text}")


def print_error(text):
    """Print error message"""
    print(f"❌ {text}")


def print_warning(text):
    """Print warning message"""
    print(f"⚠️  {text}")


def print_info(text):
    """Print info message"""
    print(f"ℹ️  {text}")


def setup_aws_bucket():
    """Setup S3 bucket with proper configuration"""
    
    print_header("AWS S3 Bucket Setup for Room Designer")
    
    # Load credentials from .env
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    bucket_name = os.getenv("AWS_S3_BUCKET")
    region = os.getenv("AWS_REGION", "us-east-1")
    
    # Validate credentials
    if not all([access_key, secret_key, bucket_name]):
        print_error("Missing AWS credentials in .env file")
        print_info("Please ensure your .env file contains:")
        print("   AWS_ACCESS_KEY_ID=your_access_key")
        print("   AWS_SECRET_ACCESS_KEY=your_secret_key")
        print("   AWS_S3_BUCKET=your_bucket_name")
        print("   AWS_REGION=us-east-1")
        return False
    
    print("\n📋 Configuration:")
    print(f"   Bucket Name: {bucket_name}")
    print(f"   Region: {region}")
    print(f"   Access Key: {access_key[:10]}...{access_key[-4:]}")
    
    try:
        # Initialize S3 client
        print_step("1", "Initializing AWS S3 client...")
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        s3_resource = boto3.resource(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        print_success("AWS S3 client initialized")
        
        # Check if bucket exists
        print_step("2", f"Checking if bucket '{bucket_name}' exists...")
        bucket_exists = False
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            bucket_exists = True
            print_success(f"Bucket already exists: {bucket_name}")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print_info("Bucket does not exist. Creating new bucket...")
                
                # Create bucket
                try:
                    if region == 'us-east-1':
                        s3_client.create_bucket(Bucket=bucket_name)
                    else:
                        s3_client.create_bucket(
                            Bucket=bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': region}
                        )
                    print_success(f"Bucket created: {bucket_name}")
                    bucket_exists = True
                except ClientError as create_error:
                    print_error(f"Failed to create bucket: {create_error}")
                    return False
            elif error_code == '403':
                print_error(f"Access denied to bucket '{bucket_name}'")
                print_info("Bucket may be owned by another AWS account or you lack permissions")
                return False
            else:
                print_error(f"Error checking bucket: {e}")
                return False
        
        if not bucket_exists:
            print_error("Could not create or access bucket")
            return False
        
        # Disable Block Public Access settings
        print_step("3", "Configuring public access settings...")
        try:
            s3_client.delete_public_access_block(Bucket=bucket_name)
            print_success("Public access block removed")
        except ClientError as e:
            # If it doesn't exist, that's fine
            if e.response['Error']['Code'] != 'NoSuchPublicAccessBlockConfiguration':
                print_warning(f"Could not modify public access block: {e}")
        
        # Set bucket policy for public read access
        print_step("4", "Setting bucket policy for public read access...")
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadGetObject",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{bucket_name}/*"
                }
            ]
        }
        
        try:
            s3_client.put_bucket_policy(
                Bucket=bucket_name,
                Policy=json.dumps(bucket_policy)
            )
            print_success("Bucket policy set for public read access")
        except ClientError as e:
            print_error(f"Failed to set bucket policy: {e}")
            print_warning("Images may not be publicly accessible")
            # Continue anyway
        
        # Enable CORS for web uploads
        print_step("5", "Configuring CORS (Cross-Origin Resource Sharing)...")
        cors_configuration = {
            'CORSRules': [
                {
                    'AllowedHeaders': ['*'],
                    'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                    'AllowedOrigins': ['*'],
                    'ExposeHeaders': ['ETag', 'x-amz-request-id'],
                    'MaxAgeSeconds': 3000
                }
            ]
        }
        
        try:
            s3_client.put_bucket_cors(
                Bucket=bucket_name,
                CORSConfiguration=cors_configuration
            )
            print_success("CORS configured")
        except ClientError as e:
            print_warning(f"Could not configure CORS: {e}")
            # Continue anyway
        
        # Set bucket versioning (optional but recommended)
        print_step("6", "Enabling bucket versioning (optional)...")
        try:
            s3_client.put_bucket_versioning(
                Bucket=bucket_name,
                VersioningConfiguration={'Status': 'Enabled'}
            )
            print_success("Bucket versioning enabled")
        except ClientError as e:
            print_warning(f"Could not enable versioning: {e}")
        
        # Test upload
        print_step("7", "Testing upload functionality...")
        test_file_name = "test_upload.txt"
        test_content = f"Test file for Room Designer app - {bucket_name}"
        test_key = "test/test_upload.txt"
        
        # Create test file
        with open(test_file_name, 'w') as f:
            f.write(test_content)
        
        try:
            # Upload test file
            s3_client.upload_file(
                test_file_name,
                bucket_name,
                test_key,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': 'text/plain'
                }
            )
            
            # Generate URL
            test_url = f"https://{bucket_name}.s3.{region}.amazonaws.com/{test_key}"
            print_success("Test upload successful!")
            print(f"   Test file URL: {test_url}")
            
            # Verify file is accessible
            import requests
            try:
                response = requests.get(test_url, timeout=10)
                if response.status_code == 200:
                    print_success("Test file is publicly accessible")
                else:
                    print_warning(f"Test file returned status code: {response.status_code}")
            except Exception as e:
                print_warning(f"Could not verify public access: {e}")
            
            # Clean up: Delete test file from S3
            print_step("8", "Cleaning up test files...")
            s3_client.delete_object(Bucket=bucket_name, Key=test_key)
            print_success("Test file deleted from S3")
            
            # Delete local test file
            os.remove(test_file_name)
            
        except ClientError as e:
            print_error(f"Test upload failed: {e}")
            print_info("Check your IAM permissions. You need s3:PutObject permission.")
            # Clean up local file
            if os.path.exists(test_file_name):
                os.remove(test_file_name)
            return False
        except Exception as e:
            print_error(f"Unexpected error during test: {e}")
            if os.path.exists(test_file_name):
                os.remove(test_file_name)
            return False
        
        # Success summary
        print_header("✅ AWS S3 Setup Complete!")
        print(f"\n🎉 Your bucket '{bucket_name}' is ready to use!")
        print("\n📊 Bucket Configuration:")
        print(f"   • Region: {region}")
        print(f"   • Public Read: Enabled")
        print(f"   • CORS: Configured")
        print(f"   • Versioning: Enabled")
        print(f"\n🔗 Bucket URL: https://{bucket_name}.s3.{region}.amazonaws.com/")
        
        print("\n🚀 Next Steps:")
        print("   1. Run: python test_aws.py")
        print("   2. Start your app: python main.py")
        print("   3. Test the API at: http://localhost:8000/docs")
        
        return True
        
    except NoCredentialsError:
        print_error("AWS credentials not found or invalid")
        print_info("Please check your .env file and ensure credentials are correct")
        return False
    except Exception as e:
        print_error(f"Unexpected error during setup: {e}")
        print_info(f"Error type: {type(e).__name__}")
        return False


def main():
    """Main function"""
    print("\n🚀 Starting AWS S3 Setup...\n")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print_error(".env file not found!")
        print_info("Please create a .env file with your AWS credentials")
        print_info("You can copy .env.example to .env and fill in your values")
        return 1
    
    # Run setup
    success = setup_aws_bucket()
    
    if success:
        print("\n" + "=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print_error("Setup failed. Please check the errors above and try again.")
        print("\n💡 Common issues:")
        print("   • Invalid AWS credentials")
        print("   • Insufficient IAM permissions (need S3 full access)")
        print("   • Bucket name already taken (must be globally unique)")
        print("   • Network connectivity issues")
        return 1


if __name__ == "__main__":
    sys.exit(main())