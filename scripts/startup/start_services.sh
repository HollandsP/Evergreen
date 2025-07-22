#!/bin/bash

echo "🚀 Starting AI Content Pipeline Services"
echo "========================================"

# Export alternative ports to avoid conflicts
export DB_PORT=5433
export REDIS_PORT=6380
export FLOWER_PORT=5556

echo "📋 Using custom ports to avoid conflicts:"
echo "   PostgreSQL: 5433 (instead of 5432)"
echo "   Redis: 6380 (instead of 6379)"
echo "   Flower: 5556 (instead of 5555)"
echo ""

# Update DATABASE_URL in .env to use new port
if [ -f .env ]; then
    # Backup original .env
    cp .env .env.backup
    
    # Update DATABASE_URL if it exists
    if grep -q "DATABASE_URL=" .env; then
        sed -i 's/:5432/:5433/g' .env
    else
        echo "DATABASE_URL=postgresql://pipeline:pipeline@localhost:5433/pipeline" >> .env
    fi
fi

echo "🐳 Starting Docker services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎯 Access Points:"
echo "   API Documentation: http://localhost:8000/docs"
echo "   Flower (Celery Monitor): http://localhost:5556"
echo "   Health Check: http://localhost:8000/health"
echo ""
echo "   Default Flower credentials: admin/admin"
echo ""

# Test API health
echo "🏥 Testing API health..."
curl -s http://localhost:8000/health | python3 -m json.tool || echo "API not ready yet"

echo ""
echo "✅ Services started! You can now:"
echo "   1. Monitor tasks at http://localhost:5556"
echo "   2. Test API at http://localhost:8000/docs"
echo "   3. Run: python3 test_services.py"
echo "   4. Generate video: python3 generate_video.py"
echo ""