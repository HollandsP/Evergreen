# 🚀 Production Deployment Guide
## Evergreen AI Content Pipeline - Complete Deployment Instructions

**Last Updated**: July 22, 2025  
**Version**: 2.0 (Post-Improvement Cycles)  
**Status**: Production Ready ✅  

---

## 📋 Prerequisites

### System Requirements
- **Node.js**: 18.0.0 or higher
- **Docker**: 20.10.0 or higher
- **Docker Compose**: 2.0.0 or higher
- **RAM**: Minimum 8GB (16GB recommended for video processing)
- **Storage**: 50GB+ available space
- **Network**: Stable internet connection for AI API calls

### Required API Keys
```bash
# AI Service API Keys (Required)
ELEVENLABS_API_KEY="your_elevenlabs_key_here"
OPENAI_API_KEY="your_openai_key_here"
RUNWAY_API_KEY="your_runway_key_here"

# Database & Cache (Auto-configured in Docker)
DATABASE_URL="postgresql://user:password@db:5432/pipeline"
REDIS_URL="redis://redis:6379"

# Optional Monitoring
SENTRY_DSN="your_sentry_dsn_here"
ANALYTICS_KEY="your_analytics_key_here"
```

---

## 🚀 Quick Start Deployment

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/your-org/evergreen-ai-pipeline.git
cd evergreen-ai-pipeline/web

# Copy environment template
cp .env.example .env

# Configure your API keys in .env
nano .env
```

### 2. Environment Configuration
Create your `.env` file with the following structure:

```bash
# Production Configuration
NODE_ENV=production
NEXT_PUBLIC_APP_ENV=production

# Application URLs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8001

# AI Service API Keys
ELEVENLABS_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
RUNWAY_API_KEY=your_key_here

# Database Configuration
DATABASE_URL=postgresql://pipeline:secure_password@db:5432/pipeline
REDIS_URL=redis://redis:6379

# Security Configuration
JWT_SECRET=your_jwt_secret_here
CORS_ORIGIN=https://your-domain.com

# Performance Configuration
MAX_CONCURRENT_GENERATIONS=5
CACHE_TTL=300000
API_TIMEOUT=60000

# Monitoring (Optional)
SENTRY_DSN=your_sentry_dsn
ANALYTICS_ENABLED=true
```

### 3. Docker Deployment
```bash
# Build and start all services
docker-compose up -d --build

# Wait for services to initialize (2-3 minutes)
docker-compose logs -f web

# Verify deployment
curl http://localhost:3000/api/health
```

### 4. Health Check
```bash
# Check all services are running
docker-compose ps

# Verify web interface
open http://localhost:3000

# Check API endpoints
curl http://localhost:3000/api/health
curl http://localhost:3000/api/status
```

---

## 🏗️ Detailed Deployment Steps

### Step 1: Infrastructure Preparation

#### 1.1 Server Setup
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### 1.2 Firewall Configuration
```bash
# Open required ports
sudo ufw allow 22/tcp      # SSH
sudo ufw allow 80/tcp      # HTTP
sudo ufw allow 443/tcp     # HTTPS
sudo ufw allow 3000/tcp    # Web Application
sudo ufw enable
```

### Step 2: Application Configuration

#### 2.1 Environment Variables Setup
```bash
# Create production environment file
cat > .env.production << 'EOF'
# Production Environment Configuration
NODE_ENV=production
NEXT_PUBLIC_APP_ENV=production

# Application Configuration
PORT=3000
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_WS_URL=wss://ws.yourdomain.com

# AI Service Configuration
ELEVENLABS_API_KEY=your_elevenlabs_api_key
OPENAI_API_KEY=your_openai_api_key
RUNWAY_API_KEY=your_runway_api_key

# Database Configuration
DATABASE_URL=postgresql://pipeline:secure_password@db:5432/pipeline
REDIS_URL=redis://redis:6379/0

# Security Configuration
JWT_SECRET=your_super_secure_jwt_secret_here
CORS_ORIGIN=https://yourdomain.com
SESSION_SECRET=your_session_secret_here

# Performance Tuning
MAX_CONCURRENT_GENERATIONS=10
CACHE_TTL=600000
API_TIMEOUT=120000
WORKER_CONCURRENCY=4

# Monitoring and Logging
SENTRY_DSN=your_sentry_dsn_here
LOG_LEVEL=info
ANALYTICS_ENABLED=true
ERROR_REPORTING=true

# Storage Configuration
UPLOAD_MAX_SIZE=100MB
STORAGE_BACKEND=local
CLEANUP_INTERVAL=3600000
EOF
```

#### 2.2 Docker Compose Production Configuration
```bash
# Create production docker-compose file
cat > docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  web:
    build: 
      context: .
      dockerfile: Dockerfile.prod
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    env_file:
      - .env.production
    depends_on:
      - db
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: pipeline
      POSTGRES_USER: pipeline
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pipeline"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
EOF
```

### Step 3: SSL/TLS Configuration

#### 3.1 Generate SSL Certificates
```bash
# Using Let's Encrypt (recommended)
sudo apt install certbot
sudo certbot certonly --standalone -d yourdomain.com

# Or generate self-signed for development
mkdir ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/private.key \
  -out ssl/certificate.crt
```

#### 3.2 Nginx Configuration
```bash
# Create nginx configuration
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream web_app {
        server web:3000;
    }

    # HTTP redirect to HTTPS
    server {
        listen 80;
        server_name yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name yourdomain.com;

        ssl_certificate /etc/nginx/ssl/certificate.crt;
        ssl_certificate_key /etc/nginx/ssl/private.key;
        
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains";

        # Gzip compression
        gzip on;
        gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

        # File upload size
        client_max_body_size 100M;

        location / {
            proxy_pass http://web_app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # WebSocket support
        location /socket.io/ {
            proxy_pass http://web_app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
EOF
```

### Step 4: Production Build & Deployment

#### 4.1 Build Production Image
```bash
# Create production Dockerfile
cat > Dockerfile.prod << 'EOF'
FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache \
    curl \
    ffmpeg \
    python3 \
    make \
    g++

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && npm cache clean --force

# Copy application code
COPY . .

# Build application
RUN npm run build

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001

# Set permissions
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1

# Start application
CMD ["npm", "start"]
EOF
```

#### 4.2 Deploy to Production
```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to start
sleep 60

# Run health checks
docker-compose -f docker-compose.prod.yml exec web curl -f http://localhost:3000/api/health

# Check logs
docker-compose -f docker-compose.prod.yml logs -f --tail=50
```

---

## 📊 Monitoring & Maintenance

### Performance Monitoring
```bash
# Monitor application performance
docker stats

# Check application logs
docker-compose -f docker-compose.prod.yml logs -f web

# Monitor database performance
docker-compose -f docker-compose.prod.yml exec db psql -U pipeline -c "SELECT * FROM pg_stat_activity;"

# Monitor Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli info
```

### Health Check Endpoints
```bash
# Application health
curl https://yourdomain.com/api/health

# Detailed status
curl https://yourdomain.com/api/status

# Database connectivity
curl https://yourdomain.com/api/db/health

# AI services status
curl https://yourdomain.com/api/services/health
```

### Log Management
```bash
# Configure log rotation
cat > /etc/logrotate.d/evergreen-pipeline << 'EOF'
/var/log/evergreen/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 www-data www-data
    postrotate
        docker-compose -f /path/to/docker-compose.prod.yml exec web kill -USR1 1
    endscript
}
EOF
```

---

## 🔧 Troubleshooting Guide

### Common Issues & Solutions

#### Issue 1: Application Won't Start
```bash
# Check Docker status
docker-compose -f docker-compose.prod.yml ps

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs web

# Verify environment variables
docker-compose -f docker-compose.prod.yml exec web env | grep -E "NODE_ENV|API_KEY"

# Restart services
docker-compose -f docker-compose.prod.yml restart web
```

#### Issue 2: Database Connection Errors
```bash
# Check database status
docker-compose -f docker-compose.prod.yml exec db pg_isready -U pipeline

# Reset database connection
docker-compose -f docker-compose.prod.yml restart db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db
```

#### Issue 3: AI Service API Errors
```bash
# Test API keys
curl -H "Authorization: Bearer $ELEVENLABS_API_KEY" https://api.elevenlabs.io/v1/voices

# Check rate limits
docker-compose -f docker-compose.prod.yml logs web | grep "rate limit"

# Verify environment variables
docker-compose -f docker-compose.prod.yml exec web echo $ELEVENLABS_API_KEY
```

#### Issue 4: Performance Problems
```bash
# Check resource usage
docker stats

# Monitor database queries
docker-compose -f docker-compose.prod.yml exec db psql -U pipeline -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"

# Clear Redis cache
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL
```

### Performance Optimization
```bash
# Optimize database
docker-compose -f docker-compose.prod.yml exec db psql -U pipeline -c "VACUUM ANALYZE;"

# Clear application cache
curl -X POST https://yourdomain.com/api/cache/clear

# Restart services for memory cleanup
docker-compose -f docker-compose.prod.yml restart
```

---

## 🔄 Backup & Recovery

### Automated Backup Script
```bash
#!/bin/bash
# backup.sh - Automated backup script

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Database backup
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U pipeline pipeline > "$BACKUP_DIR/db_backup_$DATE.sql"

# Application data backup
tar -czf "$BACKUP_DIR/app_data_$DATE.tar.gz" uploads/ logs/

# Cleanup old backups (keep last 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Recovery Procedures
```bash
# Restore database
docker-compose -f docker-compose.prod.yml exec -T db psql -U pipeline pipeline < /backups/db_backup_YYYYMMDD_HHMMSS.sql

# Restore application data
tar -xzf /backups/app_data_YYYYMMDD_HHMMSS.tar.gz

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

---

## 📈 Scaling & Load Balancing

### Horizontal Scaling
```bash
# Scale web application
docker-compose -f docker-compose.prod.yml up -d --scale web=3

# Update nginx upstream configuration
# Add multiple server entries:
# upstream web_app {
#     server web_1:3000;
#     server web_2:3000;
#     server web_3:3000;
# }
```

### Database Optimization
```sql
-- Optimize PostgreSQL for production
-- Add to postgresql.conf

shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 16MB
maintenance_work_mem = 64MB
max_connections = 100
```

### Redis Configuration
```bash
# Optimize Redis for production
echo "maxmemory 512mb" >> redis.conf
echo "maxmemory-policy allkeys-lru" >> redis.conf
```

---

## 🔐 Security Hardening

### System Security
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Install fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Application Security
```bash
# Set secure file permissions
chmod 600 .env.production
chmod 700 ssl/

# Rotate secrets regularly
openssl rand -base64 32  # New JWT secret
openssl rand -base64 32  # New session secret
```

---

## 📋 Production Checklist

### Pre-Deployment ✅
- [ ] All environment variables configured
- [ ] SSL certificates installed
- [ ] Database migrations completed
- [ ] Backup procedures tested
- [ ] Monitoring setup verified
- [ ] Load testing completed
- [ ] Security audit passed

### Post-Deployment ✅
- [ ] Health checks passing
- [ ] Performance monitoring active
- [ ] Error tracking configured
- [ ] Backup automation running
- [ ] User acceptance testing completed
- [ ] Documentation updated
- [ ] Team training completed

### Ongoing Maintenance ✅
- [ ] Regular security updates
- [ ] Database maintenance
- [ ] Performance optimization
- [ ] Backup verification
- [ ] Monitoring review
- [ ] Cost optimization
- [ ] Feature enhancement planning

---

## 📞 Support & Resources

### Emergency Contacts
- **Technical Issues**: tech-support@yourdomain.com
- **Infrastructure**: devops@yourdomain.com
- **Security Incidents**: security@yourdomain.com

### Documentation Links
- **API Documentation**: https://api.yourdomain.com/docs
- **User Guide**: https://docs.yourdomain.com/user-guide
- **Admin Guide**: https://docs.yourdomain.com/admin-guide
- **Troubleshooting**: https://docs.yourdomain.com/troubleshooting

### External Resources
- **ElevenLabs API**: https://docs.elevenlabs.io/
- **OpenAI API**: https://platform.openai.com/docs/
- **Runway API**: https://docs.runwayml.com/

---

## 🎉 Conclusion

Your Evergreen AI Content Pipeline is now successfully deployed to production! 🚀

The system is configured with:
- ✅ Enterprise-grade security
- ✅ High availability and load balancing
- ✅ Comprehensive monitoring and alerting
- ✅ Automated backup and recovery
- ✅ Performance optimization
- ✅ Scalability configuration

For ongoing support and feature requests, please refer to the documentation links above or contact our support team.

**Happy video generating!** 🎬✨

---

*Last updated: July 22, 2025*  
*Version: 2.0 (Production Ready)*  
*Next review: Monthly operational review*