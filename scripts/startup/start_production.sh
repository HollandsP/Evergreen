#!/bin/bash

echo "🚀 Starting AI Content Pipeline (Production Mode)"
echo "==============================================="

# Clean up any existing containers
echo "🧹 Cleaning up existing containers..."
docker-compose down 2>/dev/null

# Set production environment
export APP_ENV=production
export DEBUG=false
export DB_PORT=5433
export REDIS_PORT=6380
export FLOWER_PORT=5556

echo ""
echo "📋 Configuration:"
echo "   Mode: Production"
echo "   PostgreSQL: localhost:5433"
echo "   Redis: localhost:6380"
echo "   API: localhost:8000"
echo "   Flower: localhost:5556"

# Start services using only the main docker-compose.yml
echo ""
echo "🐳 Starting Docker services..."
docker-compose -f docker-compose.yml up -d

echo ""
echo "⏳ Waiting for database to be ready..."
sleep 10

echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🏥 Checking service health..."
# Check database
docker-compose exec -T db pg_isready -U pipeline -d pipeline && echo "   ✅ Database is ready" || echo "   ⚠️  Database is starting..."

# Check Redis
docker-compose exec -T redis redis-cli ping | grep -q PONG && echo "   ✅ Redis is ready" || echo "   ⚠️  Redis is starting..."

echo ""
echo "🎯 Access Points:"
echo "   • Flower (Task Monitor): http://localhost:5556"
echo "     Username: admin | Password: admin"
echo ""
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"
echo ""

# Wait a bit more for API to start
sleep 5

# Test API
echo "🔍 Testing API..."
if curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null; then
    echo "   ✅ API is ready!"
else
    echo "   ⏳ API is still starting up..."
    echo "   Check again in a few seconds"
fi

echo ""
echo "📺 To watch video generation progress:"
echo "   1. Open http://localhost:5556 in your browser"
echo "   2. Login with admin/admin"
echo "   3. You'll see real-time task progress"
echo ""
echo "🎬 Ready to generate your video!"
echo "   Run: python3 generate_video.py"
echo ""