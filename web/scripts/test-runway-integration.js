/**
 * Test script for RunwayML integration
 * Run with: node scripts/test-runway-integration.js
 */

const fetch = require('node-fetch');
const path = require('path');
const fs = require('fs');

// Load environment variables from .env file
const envPath = path.join(__dirname, '../../../.env');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  envContent.split('\n').forEach(line => {
    const [key, value] = line.split('=');
    if (key && value) {
      process.env[key.trim()] = value.trim();
    }
  });
}

// Configuration
const API_KEY = process.env.RUNWAY_API_KEY;
const BASE_URL = 'https://api.dev.runwayml.com';
const API_VERSION = '2024-11-06';

if (!API_KEY) {
  console.error('❌ RUNWAY_API_KEY not found in environment variables');
  process.exit(1);
}

// Test image URL (you can replace with your own)
const TEST_IMAGE_URL = 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=1280&h=720';

async function testRunwayAPI() {
  console.log('Testing RunwayML API Integration...\n');

  // 1. Test Organization Info
  console.log('1. Testing Organization Info...');
  try {
    const orgResponse = await fetch(`${BASE_URL}/v1/organization`, {
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'X-Runway-Version': API_VERSION,
      }
    });

    if (orgResponse.ok) {
      const orgData = await orgResponse.json();
      console.log('✅ Organization info retrieved:', orgData);
    } else {
      console.log('❌ Failed to get organization info:', orgResponse.status);
    }
  } catch (error) {
    console.log('❌ Organization info error:', error.message);
  }

  // 2. Test Image to Video Generation
  console.log('\n2. Testing Image to Video Generation...');
  try {
    const videoPayload = {
      promptImage: TEST_IMAGE_URL,
      promptText: 'Camera slowly pans right across the mountain landscape, cinematic quality, golden hour lighting',
      model: 'gen4_turbo',
      ratio: '1280:720',
      duration: 5
    };

    console.log('Request payload:', JSON.stringify(videoPayload, null, 2));

    const videoResponse = await fetch(`${BASE_URL}/v1/image_to_video`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${API_KEY}`,
        'X-Runway-Version': API_VERSION,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(videoPayload)
    });

    const responseText = await videoResponse.text();
    console.log('Response status:', videoResponse.status);
    console.log('Response headers:', videoResponse.headers.raw());
    
    let videoData;
    try {
      videoData = JSON.parse(responseText);
    } catch (e) {
      console.log('Response text:', responseText);
      throw new Error('Failed to parse response as JSON');
    }

    if (videoResponse.ok) {
      console.log('✅ Video generation task created:', videoData);
      
      // 3. Poll for task status
      if (videoData.id) {
        console.log('\n3. Polling for task completion...');
        let attempts = 0;
        const maxAttempts = 60; // 5 minutes with 5 second intervals
        
        while (attempts < maxAttempts) {
          await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
          
          const statusResponse = await fetch(`${BASE_URL}/v1/tasks/${videoData.id}`, {
            headers: {
              'Authorization': `Bearer ${API_KEY}`,
              'X-Runway-Version': API_VERSION,
            }
          });

          if (statusResponse.ok) {
            const statusData = await statusResponse.json();
            console.log(`Attempt ${attempts + 1}: Status = ${statusData.status}`);
            
            if (statusData.status === 'SUCCEEDED') {
              console.log('✅ Video generated successfully!');
              console.log('Video URL:', statusData.output?.[0]);
              break;
            } else if (statusData.status === 'FAILED') {
              console.log('❌ Video generation failed:', statusData.failure);
              break;
            }
          } else {
            console.log('❌ Failed to check status:', statusResponse.status);
          }
          
          attempts++;
        }
        
        if (attempts >= maxAttempts) {
          console.log('⏱️ Timed out waiting for video generation');
        }
      }
    } else {
      console.log('❌ Failed to create video task:', videoData);
    }
  } catch (error) {
    console.log('❌ Video generation error:', error.message);
    console.log('Stack trace:', error.stack);
  }
}

// Run the test
testRunwayAPI().catch(console.error);