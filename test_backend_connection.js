#!/usr/bin/env node

/**
 * Test script to verify backend connection
 * Run this after starting both frontend and backend servers
 */

console.log('Testing Evergreen Backend Connection...\n');

// Test 1: Check if Python API is accessible
console.log('1. Testing Python API connection...');
fetch('http://localhost:8000/api/v1/editor/health')
  .then(res => {
    if (res.ok) {
      console.log('✅ Python API is accessible');
      return res.json();
    } else {
      console.log('❌ Python API returned error:', res.status);
    }
  })
  .then(data => {
    if (data) console.log('   Response:', data);
  })
  .catch(err => {
    console.log('❌ Failed to connect to Python API');
    console.log('   Error:', err.message);
    console.log('\n💡 Make sure to start the Python backend:');
    console.log('   cd /path/to/evergreen');
    console.log('   python -m uvicorn api.main:app --reload --port 8000\n');
  });

// Test 2: Check if Next.js API proxy works
setTimeout(() => {
  console.log('\n2. Testing Next.js API proxy...');
  fetch('http://localhost:3000/api/editor/process-command', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      command: 'test connection',
      projectId: 'test-project'
    })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success === false && data.suggestions) {
        console.log('✅ Next.js API endpoint is working');
        console.log('   Response:', data.message);
      } else {
        console.log('✅ Full pipeline connected!');
        console.log('   Response:', data);
      }
    })
    .catch(err => {
      console.log('❌ Failed to connect to Next.js API');
      console.log('   Error:', err.message);
      console.log('\n💡 Make sure to start the Next.js frontend:');
      console.log('   cd web');
      console.log('   npm run dev\n');
    });
}, 1000);

// Test 3: Check WebSocket connection
setTimeout(() => {
  console.log('\n3. Testing WebSocket connection...');
  
  try {
    const WebSocket = require('ws');
    const ws = new WebSocket('ws://localhost:8000/ws?client_id=test-client');
    
    ws.on('open', () => {
      console.log('✅ WebSocket connected to Python backend');
      ws.close();
    });
    
    ws.on('error', (err) => {
      console.log('❌ WebSocket connection failed');
      console.log('   Error:', err.message);
    });
  } catch (err) {
    console.log('⚠️  WebSocket test skipped (ws module not installed)');
    console.log('   Run: npm install -g ws');
  }
}, 2000);

// Summary
setTimeout(() => {
  console.log('\n' + '='.repeat(50));
  console.log('Connection Test Summary:');
  console.log('='.repeat(50));
  console.log('\nTo start the complete pipeline:');
  console.log('\n1. Start Python backend:');
  console.log('   cd /path/to/evergreen');
  console.log('   python -m uvicorn api.main:app --reload --port 8000');
  console.log('\n2. Start Next.js frontend:');
  console.log('   cd web');
  console.log('   npm run dev');
  console.log('\n3. Access the application:');
  console.log('   http://localhost:3000/production');
  console.log('\n' + '='.repeat(50));
}, 3000);