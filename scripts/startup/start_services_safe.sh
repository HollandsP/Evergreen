#!/bin/bash

echo "🚀 Starting AI Content Pipeline Services (Safe Mode)"
echo "==================================================="

# First, stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose down

# Check what's using our ports
echo ""
echo "🔍 Checking for port conflicts..."
for port in 5432 5433 6379 6380 8000 5555 5556; do
    if lsof -i :$port &>/dev/null || netstat -tlnp 2>/dev/null | grep -q ":$port "; then
        echo "   ⚠️  Port $port is in use"
    else
        echo "   ✅ Port $port is available"
    fi
done

# Create a temporary override file with custom ports
echo ""
echo "📝 Creating custom port configuration..."
cat > docker-compose.custom.yml << 'EOF'
version: '3.8'

services:
  db:
    ports:
      - "5433:5432"  # Use 5433 externally, 5432 internally
  
  redis:
    ports:
      - "6380:6379"  # Use 6380 externally, 6379 internally
  
  flower:
    ports:
      - "5556:5555"  # Use 5556 externally, 5555 internally
EOF

echo "🐳 Starting services with custom configuration..."
# Use both override files, with custom taking precedence
docker-compose -f docker-compose.yml -f docker-compose.override.yml -f docker-compose.custom.yml up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 15

echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎯 Access Points:"
echo "   API Documentation: http://localhost:8000/docs"
echo "   Flower (Celery Monitor): http://localhost:5556"
echo "   Health Check: http://localhost:8000/health"
echo "   Database (Adminer): http://localhost:8080"
echo ""
echo "   Flower credentials: admin/admin"
echo "   Database: postgresql://pipeline:pipeline@localhost:5433/pipeline"
echo ""

# Test API health
echo "🏥 Testing API health..."
curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "   API is starting up..."

echo ""
echo "📺 Progress Monitoring UI Options:"
echo ""
echo "1. 🌸 Flower (Celery Task Monitor) - http://localhost:5556"
echo "   - Real-time task progress"
echo "   - Worker status"
echo "   - Task history and results"
echo "   - Login: admin/admin"
echo ""
echo "2. 📚 FastAPI Interactive Docs - http://localhost:8000/docs"
echo "   - Test API endpoints"
echo "   - Submit video generation requests"
echo "   - Check task status"
echo ""
echo "3. 🗄️ Adminer (Database UI) - http://localhost:8080"
echo "   - View project data"
echo "   - Check job status"
echo "   - Server: db, Username: pipeline, Password: pipeline"
echo ""
echo "✅ Services are starting! You can now:"
echo "   1. Open http://localhost:5556 to watch task progress"
echo "   2. Run: python3 test_services.py to test APIs"
echo "   3. Run: python3 generate_video.py to start video generation"
echo ""