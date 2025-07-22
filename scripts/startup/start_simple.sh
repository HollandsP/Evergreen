#!/bin/bash

echo "🚀 Starting AI Content Pipeline (Simple Mode)"
echo "==========================================="

# Clean up
echo "🧹 Cleaning up..."
docker-compose -f docker-compose.simple.yml down 2>/dev/null

# Build if needed
echo "🔨 Building Docker image..."
docker-compose -f docker-compose.simple.yml build

# Start services
echo "🐳 Starting services..."
docker-compose -f docker-compose.simple.yml up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 15

# Show status
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.simple.yml ps

echo ""
echo "🎯 Progress Monitoring UI:"
echo ""
echo "📺 Flower (Celery Monitor): http://localhost:5556"
echo "   • Real-time task progress bars"
echo "   • Worker status and health"
echo "   • Task success/failure tracking"
echo "   • Username: admin, Password: admin"
echo ""
echo "📚 API Docs: http://localhost:8000/docs"
echo "   • Test endpoints interactively"
echo "   • Submit video generation requests"
echo ""

# Quick health check
echo "🏥 Testing services..."
echo -n "   Database: "
docker exec evergreen-db pg_isready -U pipeline -d pipeline 2>/dev/null && echo "✅ Ready" || echo "⚠️  Starting..."

echo -n "   Redis: "
docker exec evergreen-redis redis-cli ping 2>/dev/null | grep -q PONG && echo "✅ Ready" || echo "⚠️  Starting..."

echo -n "   API: "
curl -s http://localhost:8000/health >/dev/null 2>&1 && echo "✅ Ready" || echo "⚠️  Starting..."

echo ""
echo "✨ Services are starting!"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:5556 to watch progress"
echo "2. Run: python3 test_services.py"
echo "3. Run: python3 generate_video.py"
echo ""