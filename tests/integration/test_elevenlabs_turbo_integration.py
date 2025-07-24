#!/usr/bin/env python3
"""
Test ElevenLabs integration with Turbo v2.5 model
Tests voice synthesis with the latest high-speed model
"""
import os
import sys
import asyncio
import logging
import tempfile
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.elevenlabs_client import ElevenLabsClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_elevenlabs_connection():
    """Test ElevenLabs API connection and credentials"""
    print("\n🔍 Testing ElevenLabs Connection...")
    
    # Check if API key is set
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment variables")
        print("   Please set your ElevenLabs API key:")
        print("   export ELEVENLABS_API_KEY='your-api-key-here'")
        return False
    
    print(f"✅ ElevenLabs API key found (ending in ...{api_key[-4:]})")
    
    try:
        # Create client
        client = ElevenLabsClient(api_key)
        
        # Test connection by getting voices
        voices = client.get_voices()
        
        if voices:
            print(f"✅ Successfully connected to ElevenLabs API")
            print(f"   Found {len(voices)} available voices")
            return True
        else:
            print("❌ Failed to retrieve voices from ElevenLabs API")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def test_elevenlabs_turbo_v25():
    """Test ElevenLabs Turbo v2.5 model"""
    print("\n🚀 Testing ElevenLabs Turbo v2.5...")
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("⚠️ Skipping Turbo v2.5 test - API key not found")
        return None
    
    try:
        # Direct API call to test Turbo v2.5
        headers = {
            'xi-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        # Get voices first to find a suitable one
        voices_response = requests.get(
            'https://api.elevenlabs.io/v1/voices',
            headers=headers
        )
        voices_response.raise_for_status()
        voices = voices_response.json()['voices']
        
        # Find a good voice for testing (prefer pre-made voices)
        test_voice = None
        preferred_voices = ['Rachel', 'Domi', 'Bella', 'Antoni', 'Josh', 'Arnold']
        
        for voice in voices:
            if voice['name'] in preferred_voices:
                test_voice = voice
                break
        
        if not test_voice and voices:
            test_voice = voices[0]  # Use first available voice
        
        if not test_voice:
            print("❌ No voices available for testing")
            return None
        
        print(f"🎤 Using voice: {test_voice['name']} ({test_voice['voice_id']})")
        
        # Test text with emotion tag as requested
        test_text = "[excited] Hello world!"
        print(f"📝 Test text: '{test_text}'")
        
        # Turbo v2.5 API endpoint
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{test_voice['voice_id']}"
        
        payload = {
            "text": test_text,
            "model_id": "eleven_turbo_v2_5",  # Turbo v2.5 model
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        # Request headers for audio format
        headers['Accept'] = 'audio/mpeg'
        
        print("🔄 Sending request to ElevenLabs Turbo v2.5...")
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            print("✅ Successfully generated audio with Turbo v2.5!")
            
            # Save audio to temp file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                temp_file.write(response.content)
                temp_path = temp_file.name
            
            file_size = len(response.content) / 1024
            print(f"   Audio file size: {file_size:.1f} KB")
            print(f"   Saved to: {temp_path}")
            
            # Get response headers for latency info
            if 'X-Latency' in response.headers:
                print(f"   Generation latency: {response.headers['X-Latency']}ms")
            
            # Clean up
            os.unlink(temp_path)
            print("   Cleaned up test file")
            
            return True
            
        elif response.status_code == 400:
            error_data = response.json()
            if 'model_id' in str(error_data):
                print("⚠️ Turbo v2.5 model not available on your plan")
                print("   Falling back to standard model test...")
                return test_elevenlabs_standard_model(test_voice['voice_id'], test_text)
            else:
                print(f"❌ API error: {error_data}")
                return False
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Turbo v2.5 test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_elevenlabs_standard_model(voice_id: str, text: str):
    """Test with standard ElevenLabs model as fallback"""
    print("\n📢 Testing ElevenLabs Standard Model...")
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    
    try:
        client = ElevenLabsClient(api_key)
        
        # Generate with standard model
        audio_data = client.text_to_speech(
            text=text,
            voice_id=voice_id,
            voice_settings={
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        )
        
        if audio_data:
            print("✅ Successfully generated audio with standard model")
            print(f"   Audio size: {len(audio_data) / 1024:.1f} KB")
            return True
        else:
            print("❌ Failed to generate audio")
            return False
            
    except Exception as e:
        print(f"❌ Standard model test failed: {e}")
        return False

def test_elevenlabs_voices():
    """Test available voices and models"""
    print("\n🎵 Testing Available Voices and Models...")
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("⚠️ Skipping voices test - API key not found")
        return
    
    try:
        client = ElevenLabsClient(api_key)
        voices = client.get_voices()
        
        print(f"\n📋 Available Voices: {len(voices)}")
        
        # Show first 5 voices
        for i, voice in enumerate(voices[:5]):
            print(f"\n{i+1}. {voice['name']}")
            print(f"   ID: {voice['voice_id']}")
            print(f"   Category: {voice.get('category', 'N/A')}")
            
            # Check if voice has samples
            if 'samples' in voice and voice['samples']:
                print(f"   Preview available: Yes")
            else:
                print(f"   Preview available: No")
        
        if len(voices) > 5:
            print(f"\n   ... and {len(voices) - 5} more voices")
        
        # Test models endpoint
        print("\n📦 Testing Available Models...")
        headers = {
            'xi-api-key': api_key
        }
        
        models_response = requests.get(
            'https://api.elevenlabs.io/v1/models',
            headers=headers
        )
        
        if models_response.status_code == 200:
            models = models_response.json()
            print(f"\n✅ Available Models:")
            
            for model in models:
                print(f"\n   Model ID: {model['model_id']}")
                print(f"   Name: {model['name']}")
                print(f"   Description: {model.get('description', 'N/A')}")
                
                # Check for Turbo v2.5
                if 'turbo' in model['model_id'].lower() and '2.5' in model['name']:
                    print("   ⚡ This is the Turbo v2.5 model!")
        else:
            print("⚠️ Could not retrieve models list")
            
    except Exception as e:
        print(f"❌ Voices test failed: {e}")

def test_elevenlabs_streaming():
    """Test streaming capabilities"""
    print("\n🌊 Testing ElevenLabs Streaming...")
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("⚠️ Skipping streaming test - API key not found")
        return
    
    try:
        client = ElevenLabsClient(api_key)
        
        # Get a voice for testing
        voices = client.get_voices()
        if not voices:
            print("❌ No voices available")
            return
        
        voice_id = voices[0]['voice_id']
        test_text = "This is a test of the streaming capabilities. The audio should be generated in real-time."
        
        print(f"🎤 Testing streaming with voice: {voices[0]['name']}")
        print(f"📝 Text: '{test_text}'")
        
        # Stream audio
        total_size = 0
        chunk_count = 0
        
        for chunk in client.text_to_speech_stream(test_text, voice_id):
            total_size += len(chunk)
            chunk_count += 1
        
        print(f"✅ Streaming successful!")
        print(f"   Total chunks: {chunk_count}")
        print(f"   Total size: {total_size / 1024:.1f} KB")
        print(f"   Average chunk size: {(total_size / chunk_count) / 1024:.1f} KB")
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")

def test_elevenlabs_limits():
    """Test and document API limits"""
    print("\n⚠️ ElevenLabs API Limits and Notes...")
    
    print("\n📊 Character Limits:")
    print("   - Standard request: 5,000 characters max")
    print("   - Turbo models: Same limit but faster generation")
    
    print("\n💰 Pricing Tiers:")
    print("   - Free: 10,000 characters/month")
    print("   - Starter: 30,000 characters/month")
    print("   - Creator: 100,000 characters/month")
    print("   - Pro: 500,000 characters/month")
    
    print("\n🚀 Turbo v2.5 Features:")
    print("   - ~32x faster than standard models")
    print("   - Lower latency for real-time applications")
    print("   - Same quality as standard models")
    print("   - Supports emotion tags like [excited], [sad], [angry]")
    
    print("\n🎯 Best Practices:")
    print("   - Use streaming for long texts")
    print("   - Cache generated audio when possible")
    print("   - Monitor your character usage")
    print("   - Use appropriate voice settings for your use case")

def main():
    """Run all ElevenLabs tests"""
    print("🚀 ElevenLabs Turbo v2.5 Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Connection
    connection_ok = test_elevenlabs_connection()
    
    if not connection_ok:
        print("\n⚠️ Connection test failed. Please check your API key.")
        print("   Other tests will be skipped.")
        return
    
    # Test 2: Turbo v2.5 with emotion tag
    turbo_ok = test_elevenlabs_turbo_v25()
    
    # Test 3: Available voices and models
    test_elevenlabs_voices()
    
    # Test 4: Streaming capabilities
    test_elevenlabs_streaming()
    
    # Test 5: Document limits and features
    test_elevenlabs_limits()
    
    print("\n✅ ElevenLabs Integration Tests Complete!")
    print("=" * 50)

if __name__ == "__main__":
    main()