# test_aws.py
"""
Test AWS S3 Configuration
Verifies that AWS credentials and S3 bucket are properly configured

Usage:
    python test_aws.py
"""

import os
import sys
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_header(text):
    """Print formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_step(step_num, text):
    """Print test step"""
    print(f"\n{step_num}️⃣  {text}")


def print_success(text):
    """Print success message"""
    print(f"   ✅ {text}")


def print_error(text):
    """Print error message"""
    print(f"   ❌ {text}")


def print_info(text):
    """Print info message"""
    print(f"   ℹ️  {text}")


def test_environment_variables():
    """Test if all required environment variables are set"""
    print_step("1", "Checking environment variables...")
    
    required_vars = [
        "REPLICATE_API_TOKEN",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_S3_BUCKET",
        "AWS_REGION"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "KEY" in var or "TOKEN" in var:
                masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                print_success(f"{var}: {masked}")
            else:
                print_success(f"{var}: {value}")
        else:
            print_error(f"{var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print_error(f"Missing variables: {', '.join(missing_vars)}")
        return False
    
    return True


def test_aws_service_initialization():
    """Test AWS service initialization"""
    print_step("2", "Initializing AWS service...")
    
    try:
        from ai_backend.services.aws_service import AWSService
        
        access_key = os.getenv("AWS_ACCESS_KEY_ID")
        secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        bucket = os.getenv("AWS_S3_BUCKET")
        region = os.getenv("AWS_REGION", "us-east-1")
        
        aws_service = AWSService(access_key, secret_key, bucket, region)
        print_success("AWS service initialized")
        return aws_service
        
    except ImportError as e:
        print_error(f"Import error: {e}")
        print_info("Make sure ai_backend package is in your Python path")
        return None
    except Exception as e:
        print_error(f"Initialization failed: {e}")
        return None


def test_bucket_connection(aws_service):
    """Test connection to S3 bucket"""
    print_step("3", "Testing bucket connection...")
    
    try:
        if aws_service.test_connection():
            print_success("Successfully connected to bucket")
            return True
        else:
            print_error("Connection test failed")
            return False
    except Exception as e:
        print_error(f"Connection error: {e}")
        return False


def test_bucket_exists(aws_service):
    """Test if bucket exists"""
    print_step("4", "Checking if bucket exists...")
    
    try:
        if aws_service.bucket_exists():
            print_success(f"Bucket exists: {aws_service.bucket_name}")
            return True
        else:
            print_error(f"Bucket does not exist: {aws_service.bucket_name}")
            print_info("Run: python setup_aws.py")
            return False
    except Exception as e:
        print_error(f"Error checking bucket: {e}")
        return False


def test_file_upload(aws_service):
    """Test file upload functionality"""
    print_step("5", "Testing file upload...")
    
    # Create a test file
    test_content = "This is a test file for AWS S3 integration testing"
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            test_file_path = f.name
        
        print_info(f"Created test file: {test_file_path}")
        
        # Upload file
        url = aws_service.upload_file(
            file_path=test_file_path,
            object_name="test/integration_test.txt",
            make_public=True
        )
        
        if url:
            print_success("Upload successful")
            print_info(f"File URL: {url}")
            
            # Verify file is accessible
            print_info("Verifying public access...")
            import requests
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200 and response.text == test_content:
                print_success("File is publicly accessible and content matches")
            else:
                print_error(f"File check failed (Status: {response.status_code})")
                return False
            
            return url
        else:
            print_error("Upload returned no URL")
            return False
            
    except Exception as e:
        print_error(f"Upload test failed: {e}")
        return False
    finally:
        # Cleanup local test file
        try:
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
                print_info("Local test file deleted")
        except:
            pass


def test_file_deletion(aws_service, file_url):
    """Test file deletion"""
    print_step("6", "Testing file deletion...")
    
    try:
        # Extract object key from URL
        # URL format: https://bucket.s3.region.amazonaws.com/key
        object_key = file_url.split(".amazonaws.com/")[-1]
        
        if aws_service.delete_file(object_key):
            print_success("File deleted successfully")
            
            # Verify deletion
            import requests
            response = requests.get(file_url, timeout=10)
            if response.status_code == 404 or response.status_code == 403:
                print_success("Verified file is no longer accessible")
                return True
            else:
                print_error(f"File still accessible (Status: {response.status_code})")
                return False
        else:
            print_error("Delete operation failed")
            return False
            
    except Exception as e:
        print_error(f"Delete test failed: {e}")
        return False


def test_list_files(aws_service):
    """Test listing files"""
    print_step("7", "Testing file listing...")
    
    try:
        files = aws_service.list_files(prefix="test/")
        print_success(f"Found {len(files)} files with prefix 'test/'")
        
        if files:
            print_info("Sample files:")
            for file in files[:5]:  # Show first 5
                print(f"      - {file}")
        
        return True
        
    except Exception as e:
        print_error(f"List test failed: {e}")
        return False


def test_storage_service():
    """Test storage service wrapper"""
    print_step("8", "Testing storage service wrapper...")
    
    try:
        from ai_backend.services.storage import upload_to_s3
        
        # Create test file
        test_content = b"Test image data"
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        print_info(f"Created test file: {test_file}")
        
        # Upload using storage service
        url = upload_to_s3(test_file, folder="test")
        
        if url:
            print_success("Storage service upload successful")
            print_info(f"URL: {url}")
            return True
        else:
            print_error("Storage service upload failed")
            return False
            
    except Exception as e:
        print_error(f"Storage service test failed: {e}")
        return False


def run_all_tests():
    """Run all tests"""
    print_header("AWS S3 Configuration Test Suite")
    print("Testing all AWS S3 functionality for Room Designer\n")
    
    test_results = []
    aws_service = None
    uploaded_file_url = None
    
    # Test 1: Environment variables
    result = test_environment_variables()
    test_results.append(("Environment Variables", result))
    if not result:
        print("\n⚠️  Cannot proceed without environment variables")
        return False
    
    # Test 2: AWS service initialization
    aws_service = test_aws_service_initialization()
    test_results.append(("AWS Service Init", aws_service is not None))
    if not aws_service:
        print("\n⚠️  Cannot proceed without AWS service")
        return False
    
    # Test 3: Bucket connection
    result = test_bucket_connection(aws_service)
    test_results.append(("Bucket Connection", result))
    if not result:
        return False
    
    # Test 4: Bucket exists
    result = test_bucket_exists(aws_service)
    test_results.append(("Bucket Exists", result))
    if not result:
        return False
    
    # Test 5: File upload
    uploaded_file_url = test_file_upload(aws_service)
    test_results.append(("File Upload", uploaded_file_url is not False))
    
    # Test 6: File deletion
    if uploaded_file_url:
        result = test_file_deletion(aws_service, uploaded_file_url)
        test_results.append(("File Deletion", result))
    
    # Test 7: List files
    result = test_list_files(aws_service)
    test_results.append(("List Files", result))
    
    # Test 8: Storage service
    result = test_storage_service()
    test_results.append(("Storage Service", result))
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    print(f"\n📊 Results: {passed}/{total} tests passed\n")
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}  {test_name}")
    
    if passed == total:
        print_header("✅ All Tests Passed!")
        print("\n🎉 AWS S3 is fully configured and working!")
        print("\n🚀 You can now:")
        print("   1. Start the API: python main.py")
        print("   2. Test endpoints at: http://localhost:8000/docs")
        print("   3. Upload images and generate designs")
        return True
    else:
        print_header("❌ Some Tests Failed")
        print("\n⚠️  Please fix the failing tests before proceeding")
        print("\n💡 Common fixes:")
        print("   • Run: python setup_aws.py")
        print("   • Check AWS credentials in .env")
        print("   • Verify IAM permissions")
        return False


def main():
    """Main function"""
    try:
        success = run_all_tests()
        print("\n" + "=" * 60 + "\n")
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())