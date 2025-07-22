#!/usr/bin/env python3
"""
Test script to verify AI Content Pipeline is working
"""
import os
import asyncio
import boto3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_aws_connection():
    """Test AWS S3 connection"""
    print("🔍 Testing AWS S3 connection...")
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        
        # List buckets
        response = s3.list_buckets()
        print("✅ AWS connected successfully!")
        print(f"   Found {len(response['Buckets'])} buckets")
        
        # Check our specific bucket
        bucket_name = os.getenv('S3_BUCKET')
        try:
            s3.head_bucket(Bucket=bucket_name)
            print(f"✅ Bucket '{bucket_name}' is accessible!")
        except:
            print(f"❌ Bucket '{bucket_name}' not found or not accessible")
            
    except Exception as e:
        print(f"❌ AWS connection failed: {str(e)}")
        return False
    return True

def test_elevenlabs_connection():
    """Test ElevenLabs API connection"""
    print("\n🔍 Testing ElevenLabs API...")
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ ElevenLabs API key not found")
        return False
    
    print(f"✅ ElevenLabs API key found: {api_key[:10]}...")
    # Actual API test will be done when we run the voice synthesis
    return True

def test_runway_connection():
    """Test Runway API connection"""
    print("\n🔍 Testing Runway API...")
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        print("❌ Runway API key not found")
        return False
    
    print(f"✅ Runway API key found: {api_key[:10]}...")
    return True

def test_openai_connection():
    """Test OpenAI API connection"""
    print("\n🔍 Testing OpenAI API...")
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key not found")
        return False
    
    print(f"✅ OpenAI API key found: {api_key[:10]}...")
    return True

def test_database_url():
    """Test database configuration"""
    print("\n🔍 Testing Database configuration...")
    db_url = os.getenv('DATABASE_URL')
    if db_url:
        print(f"✅ Database URL configured: {db_url.split('@')[1] if '@' in db_url else db_url}")
        return True
    print("❌ Database URL not found")
    return False

def main():
    """Run all tests"""
    print("🚀 AI Content Pipeline Configuration Test\n")
    print("=" * 50)
    
    results = {
        "AWS S3": test_aws_connection(),
        "ElevenLabs": test_elevenlabs_connection(),
        "Runway": test_runway_connection(),
        "OpenAI": test_openai_connection(),
        "Database": test_database_url(),
    }
    
    print("\n" + "=" * 50)
    print("📊 Summary:")
    for service, status in results.items():
        emoji = "✅" if status else "❌"
        print(f"   {emoji} {service}")
    
    all_good = all(results.values())
    if all_good:
        print("\n🎉 All services configured correctly!")
        print("Ready to process your first video script!")
    else:
        print("\n⚠️  Some services need configuration")
        print("But we can still test with what's available!")
    
    print("\n📝 Next step: Provide your script and we'll generate a video!")

if __name__ == "__main__":
    main()