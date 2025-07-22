#!/usr/bin/env python3
"""
Test individual services without Docker
"""
import os
from dotenv import load_dotenv
from elevenlabs import generate, set_api_key
import httpx
import asyncio

# Load environment variables
load_dotenv()

def test_elevenlabs():
    """Test ElevenLabs API connection"""
    print("🎙️ Testing ElevenLabs API...")
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            print("❌ ElevenLabs API key not found")
            return False
            
        set_api_key(api_key)
        
        # Try to generate a simple test audio
        audio = generate(
            text="System test. Voice synthesis operational.",
            voice="Rachel",  # Default voice
            model="eleven_monolingual_v1"
        )
        
        # Save test audio
        with open("test_audio.mp3", "wb") as f:
            f.write(audio)
        
        print("✅ ElevenLabs API working! Test audio saved as test_audio.mp3")
        return True
        
    except Exception as e:
        print(f"❌ ElevenLabs API error: {str(e)}")
        return False

async def test_runway():
    """Test Runway API connection"""
    print("\n🎬 Testing Runway API...")
    try:
        api_key = os.getenv("RUNWAY_API_KEY")
        if not api_key:
            print("❌ Runway API key not found")
            return False
        
        # Runway Gen-2 API endpoint
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            # Try to get API status
            response = await client.get(
                "https://api.runwayml.com/v1/status",
                headers=headers
            )
            
            if response.status_code == 200:
                print("✅ Runway API connection successful!")
                return True
            else:
                print(f"❌ Runway API returned status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Runway API error: {str(e)}")
        return False

def test_aws_s3():
    """Test AWS S3 connection"""
    print("\n☁️ Testing AWS S3...")
    try:
        import boto3
        
        # Create S3 client
        s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            region_name=os.getenv("AWS_REGION", "us-east-2")
        )
        
        bucket_name = os.getenv("S3_BUCKET")
        if not bucket_name:
            print("❌ S3 bucket name not found")
            return False
        
        # Try to list objects in bucket
        response = s3.list_objects_v2(Bucket=bucket_name, MaxKeys=1)
        print(f"✅ AWS S3 connection successful! Bucket: {bucket_name}")
        return True
        
    except Exception as e:
        print(f"❌ AWS S3 error: {str(e)}")
        return False

def test_openai():
    """Test OpenAI API connection"""
    print("\n🤖 Testing OpenAI API...")
    try:
        import openai
        
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OpenAI API key not found")
            return False
            
        openai.api_key = api_key
        
        # Simple test completion
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say 'API test successful'"}],
            max_tokens=10
        )
        
        print(f"✅ OpenAI API working! Response: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI API error: {str(e)}")
        return False

async def main():
    """Run all tests"""
    print("🚀 AI Content Pipeline - Service Tests")
    print("=" * 50)
    
    # Test all services
    results = {
        "ElevenLabs": test_elevenlabs(),
        "OpenAI": test_openai(),
        "AWS S3": test_aws_s3(),
    }
    
    # Test async services
    results["Runway"] = await test_runway()
    
    # Summary
    print("\n📊 Test Summary:")
    print("-" * 30)
    for service, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {service}: {'Working' if status else 'Failed'}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All services are operational!")
    else:
        print("\n⚠️ Some services need attention.")
    
    return all_passed

if __name__ == "__main__":
    asyncio.run(main())