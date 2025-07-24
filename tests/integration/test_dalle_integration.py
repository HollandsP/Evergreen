#!/usr/bin/env python3
"""
Test DALL-E 3 integration for image generation
Tests basic connectivity, image generation, and API key validation
"""
import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.services.dalle3_client import OpenAIImageGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_dalle3_connection():
    """Test DALL-E 3 API connection and credentials"""
    print("\n🔍 Testing DALL-E 3 Connection...")
    
    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        print("   Please set your OpenAI API key:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        return False
    
    print(f"✅ OpenAI API key found (ending in ...{api_key[-4:]})")
    
    try:
        # Create client
        client = OpenAIImageGenerator(api_key)
        
        # Test connection
        connected = await client.test_connection()
        
        if connected:
            print("✅ Successfully connected to OpenAI API")
            return True
        else:
            print("❌ Failed to connect to OpenAI API")
            print("   Please check your API key is valid")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

async def test_dalle3_simple_generation():
    """Test simple image generation with DALL-E 3"""
    print("\n🎨 Testing DALL-E 3 Image Generation...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ Skipping generation test - API key not found")
        return None
    
    try:
        client = OpenAIImageGenerator(api_key)
        
        # Test prompt as requested
        prompt = "A red cube on white background"
        print(f"📝 Generating image with prompt: '{prompt}'")
        
        # Generate image
        result = await client.generate_image(
            prompt=prompt,
            size="1024x1024",  # Use standard size for testing to save costs
            quality="standard",
            style="natural",
            enhance_for_video=False
        )
        
        if result['success']:
            print("✅ Image generated successfully!")
            print(f"   Original URL: {result['original_url'][:50]}...")
            print(f"   Resized path: {result['resized_path']}")
            print(f"   Generation time: {result['generation_time']:.2f}s")
            print(f"   Cost: ${result['cost']:.3f}")
            print(f"   Revised prompt: {result['revised_prompt']}")
            
            # Check if resized file exists
            if os.path.exists(result['resized_path']):
                file_size = os.path.getsize(result['resized_path']) / 1024
                print(f"   Resized file size: {file_size:.1f} KB")
                
                # Clean up test file
                os.unlink(result['resized_path'])
                print("   Cleaned up test file")
            
            return result
        else:
            print(f"❌ Image generation failed: {result['error']}")
            if 'details' in result:
                print(f"   Details: {result['details']}")
            return None
            
    except Exception as e:
        print(f"❌ Generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_dalle3_video_optimized():
    """Test DALL-E 3 with video optimization features"""
    print("\n🎬 Testing DALL-E 3 Video-Optimized Generation...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ Skipping video optimization test - API key not found")
        return None
    
    try:
        client = OpenAIImageGenerator(api_key)
        
        # Test with a more cinematic prompt
        prompt = "A futuristic cityscape at sunset with flying vehicles"
        print(f"📝 Generating cinematic image: '{prompt}'")
        
        # Generate with video optimization
        result = await client.generate_image(
            prompt=prompt,
            size="1792x1024",  # HD landscape for video
            quality="hd",
            style="vivid",
            enhance_for_video=True
        )
        
        if result['success']:
            print("✅ Video-optimized image generated!")
            print(f"   Enhanced prompt: {result['revised_prompt']}")
            print(f"   Generation time: {result['generation_time']:.2f}s")
            print(f"   Cost: ${result['cost']:.3f}")
            print(f"   Target resolution: 1280x720 (optimized for video)")
            
            # Clean up
            if os.path.exists(result['resized_path']):
                os.unlink(result['resized_path'])
            
            return result
        else:
            print(f"❌ Video-optimized generation failed: {result['error']}")
            return None
            
    except Exception as e:
        print(f"❌ Video optimization test failed: {e}")
        return None

async def test_dalle3_batch_generation():
    """Test batch generation capabilities"""
    print("\n🎯 Testing DALL-E 3 Batch Generation...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ Skipping batch test - API key not found")
        return None
    
    try:
        client = OpenAIImageGenerator(api_key)
        
        # Test with multiple prompts
        prompts = [
            "A peaceful mountain landscape at dawn",
            "A bustling cyberpunk street market",
            "An abstract pattern of flowing colors"
        ]
        
        print(f"📝 Generating {len(prompts)} images in batch...")
        
        # Generate batch (will respect rate limits)
        results = await client.generate_batch(
            prompts=prompts,
            size="1024x1024",  # Standard size to save costs
            quality="standard",
            style="natural",
            enhance_for_video=False
        )
        
        success_count = sum(1 for r in results if r['success'])
        print(f"\n✅ Batch generation complete: {success_count}/{len(prompts)} successful")
        
        # Show cost summary
        cost_summary = client.get_cost_summary()
        print(f"\n💰 Cost Summary:")
        print(f"   Total cost: ${cost_summary['total_cost']:.3f}")
        print(f"   Images generated: {cost_summary['generation_count']}")
        print(f"   Average cost per image: ${cost_summary['average_cost']:.3f}")
        
        # Clean up generated files
        for result in results:
            if result['success'] and os.path.exists(result['resized_path']):
                os.unlink(result['resized_path'])
        
        return results
        
    except Exception as e:
        print(f"❌ Batch generation test failed: {e}")
        return None

async def test_dalle3_limitations():
    """Test and document DALL-E 3 limitations"""
    print("\n⚠️ Testing DALL-E 3 Limitations...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ Skipping limitations test - API key not found")
        return
    
    try:
        client = OpenAIImageGenerator(api_key)
        
        # Test 1: Variations (not supported in DALL-E 3)
        print("\n1️⃣ Testing variations (expected to fail)...")
        result = await client.generate_variations("dummy_path.jpg")
        print(f"   Result: {result['error']}")
        print(f"   Suggestion: {result['suggestion']}")
        
        # Test 2: Multiple images per request (n > 1)
        print("\n2️⃣ Testing multiple images per request...")
        print("   Note: DALL-E 3 only supports n=1 (one image per request)")
        print("   Use batch generation for multiple images")
        
        # Test 3: Content policy
        print("\n3️⃣ Content Policy Notes:")
        print("   - DALL-E 3 has strict content policies")
        print("   - Violent, adult, or hateful content will be rejected")
        print("   - Celebrity likenesses are not allowed")
        print("   - Prompts may be revised for safety")
        
        # Test 4: Rate limits
        print("\n4️⃣ Rate Limits:")
        print("   - Tier 1: 5 images per minute")
        print("   - Tier 2: 7 images per minute")
        print("   - Tier 3: 10 images per minute")
        print("   - Batch generation handles this automatically")
        
    except Exception as e:
        print(f"❌ Limitations test failed: {e}")

async def main():
    """Run all DALL-E 3 tests"""
    print("🚀 DALL-E 3 Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Connection
    connection_ok = await test_dalle3_connection()
    
    if not connection_ok:
        print("\n⚠️ Connection test failed. Please check your API key.")
        print("   Other tests will be skipped.")
        return
    
    # Test 2: Simple generation
    simple_result = await test_dalle3_simple_generation()
    
    # Test 3: Video-optimized generation (only if simple test passed)
    if simple_result:
        await test_dalle3_video_optimized()
    
    # Test 4: Batch generation (optional - costs more)
    print("\n💡 Batch generation test available but skipped to save costs")
    print("   Uncomment the line below to test batch generation:")
    # await test_dalle3_batch_generation()
    
    # Test 5: Document limitations
    await test_dalle3_limitations()
    
    print("\n✅ DALL-E 3 Integration Tests Complete!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())