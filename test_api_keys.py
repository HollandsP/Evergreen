#!/usr/bin/env python3
"""
Test script to validate all API keys
"""
import os
import sys
import requests
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

def test_elevenlabs_api():
    """Test ElevenLabs API key"""
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        return False, "No ELEVENLABS_API_KEY found in environment"
    
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "Accept": "application/json",
        "xi-api-key": api_key
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            voices = response.json().get('voices', [])
            return True, f"✅ ElevenLabs API working! Found {len(voices)} voices"
        else:
            return False, f"❌ ElevenLabs API error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"❌ ElevenLabs API exception: {str(e)}"

def test_openai_api():
    """Test OpenAI API key"""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return False, "No OPENAI_API_KEY found in environment"
    
    url = "https://api.openai.com/v1/models"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            models = response.json().get('data', [])
            return True, f"✅ OpenAI API working! Found {len(models)} models"
        else:
            return False, f"❌ OpenAI API error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"❌ OpenAI API exception: {str(e)}"

def test_runway_api():
    """Test Runway API key"""
    api_key = os.getenv('RUNWAY_API_KEY')
    if not api_key:
        return False, "No RUNWAY_API_KEY found in environment"
    
    # Note: Runway doesn't have a simple health check endpoint
    # We'll just validate the key format for now
    if api_key.startswith('key_') and len(api_key) > 100:
        return True, "✅ Runway API key format looks valid (actual API test requires job submission)"
    else:
        return False, "❌ Runway API key format appears invalid"

def test_aws_credentials():
    """Test AWS credentials"""
    access_key = os.getenv('AWS_ACCESS_KEY_ID')
    secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    
    if not access_key or not secret_key:
        return False, "Missing AWS credentials"
    
    # Basic format validation
    if access_key.startswith('AKIA') and len(access_key) == 20:
        return True, "✅ AWS credentials format looks valid"
    else:
        return False, "❌ AWS credentials format appears invalid"

def main():
    print("=== API Key Validation ===\n")
    
    # Test each API
    tests = [
        ("ElevenLabs", test_elevenlabs_api),
        ("OpenAI", test_openai_api),
        ("Runway", test_runway_api),
        ("AWS", test_aws_credentials)
    ]
    
    all_passed = True
    
    for name, test_func in tests:
        print(f"Testing {name}...")
        success, message = test_func()
        print(f"  {message}\n")
        if not success:
            all_passed = False
    
    if all_passed:
        print("✅ All API keys validated successfully!")
        return 0
    else:
        print("❌ Some API keys failed validation. Please check your .env file.")
        return 1

if __name__ == "__main__":
    sys.exit(main())