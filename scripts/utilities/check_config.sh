#!/bin/bash

echo "🚀 AI Content Pipeline Configuration Check"
echo "=========================================="

# Check if .env file exists
if [ -f .env ]; then
    echo "✅ .env file found"
    
    # Check for API keys (showing only first 10 chars for security)
    echo ""
    echo "📋 API Keys Status:"
    
    if grep -q "ELEVENLABS_API_KEY=sk_" .env; then
        echo "✅ ElevenLabs API key configured"
    else
        echo "❌ ElevenLabs API key missing or invalid"
    fi
    
    if grep -q "RUNWAY_API_KEY=key_" .env; then
        echo "✅ Runway API key configured"
    else
        echo "❌ Runway API key missing or invalid"
    fi
    
    if grep -q "OPENAI_API_KEY=sk-" .env; then
        echo "✅ OpenAI API key configured"
    else
        echo "❌ OpenAI API key missing or invalid"
    fi
    
    if grep -q "AWS_ACCESS_KEY_ID=AKIA" .env; then
        echo "✅ AWS Access Key configured"
    else
        echo "❌ AWS Access Key missing"
    fi
    
    echo ""
    echo "📦 S3 Bucket Configuration:"
    S3_BUCKET=$(grep "S3_BUCKET=" .env | cut -d'=' -f2)
    AWS_REGION=$(grep "AWS_REGION=" .env | cut -d'=' -f2)
    echo "   Bucket: $S3_BUCKET"
    echo "   Region: $AWS_REGION"
    
else
    echo "❌ .env file not found!"
fi

echo ""
echo "=========================================="
echo "✅ Ready to start Docker services and test with your script!"
echo ""
echo "Next steps:"
echo "1. Start services: docker-compose up -d"
echo "2. Provide your script for the first video"
echo ""