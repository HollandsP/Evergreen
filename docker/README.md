# Docker Configuration Guide

This directory contains alternative and specialized Docker Compose configurations for the Evergreen AI Content Pipeline project.

## Directory Structure

```
docker/
├── production/          # Production deployment configurations
├── alternative/         # Alternative architectures (e.g., RabbitMQ)
└── development/         # Development utilities and overrides
```

## Main Configurations (in project root)

### docker-compose.yml
The primary Docker Compose configuration containing the complete service stack:
- API service with FastAPI
- Celery workers (3 replicas)
- Celery Beat scheduler
- PostgreSQL database
- Redis cache/queue
- Flower monitoring
- Nginx reverse proxy (production profile)
- Database migration service

**Usage:**
```bash
# Start all services
docker-compose up -d

# Start with production profile (includes nginx)
docker-compose --profile production up -d
```

### docker-compose.override.yml
Automatically loaded development overrides:
- Hot reloading for API and workers
- Source code volume mounts
- Debug mode enabled
- Development tools (mailhog, adminer) with dev-tools profile
- Exposed ports for local development

**Usage:**
```bash
# Start with development overrides (automatic)
docker-compose up -d

# Include development tools
docker-compose --profile dev-tools up -d
```

## Alternative Configurations

### production/docker-compose.prod.yml
Production-specific overrides for deployment:
- External Docker registry support
- Enhanced resource limits
- Production logging
- External secrets
- Persistent data volumes

**Usage:**
```bash
# Deploy to production
docker-compose -f docker-compose.yml -f docker/production/docker-compose.prod.yml up -d
```

### alternative/docker-compose.celery.yml
RabbitMQ-based Celery architecture with specialized workers:
- RabbitMQ message broker (instead of Redis)
- Queue-specific workers (script, voice, video, assembly)
- Optimized concurrency per worker type

**Usage:**
```bash
# Use RabbitMQ architecture
docker-compose -f docker/alternative/docker-compose.celery.yml up -d
```

### development/docker-compose.simple.yml
Simplified stack for quick development:
- Single worker instance
- Custom ports (5433, 6380, 5556)
- Minimal configuration
- No scheduler or migration service

**Usage:**
```bash
# Simple development stack
docker-compose -f docker/development/docker-compose.simple.yml up -d
```

### development/docker-compose.custom.yml
Port remapping override for development:
- PostgreSQL: 5433 (external) → 5432 (internal)
- Redis: 6380 (external) → 6379 (internal)
- Flower: 5556 (external) → 5555 (internal)

**Usage:**
```bash
# Apply custom port mappings
docker-compose -f docker-compose.yml -f docker/development/docker-compose.custom.yml up -d
```

## Environment Variables

Create a `.env` file in the project root with required variables:

```bash
# API Keys
ELEVENLABS_API_KEY=your_key_here
RUNWAY_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here

# AWS Configuration
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_key_here
AWS_REGION=us-east-1
S3_BUCKET=content-pipeline-media

# Database (for overrides)
DB_PASSWORD=secure_password
DB_PORT=5432

# Redis (for overrides)
REDIS_PORT=6379

# Flower Authentication
FLOWER_USER=admin
FLOWER_PASSWORD=admin
FLOWER_BASIC_AUTH=admin:password

# Production Settings
DOCKER_REGISTRY=docker.io
DOCKER_IMAGE=evergreen-pipeline
VERSION=latest

# RabbitMQ (for Celery alternative)
RABBITMQ_USER=admin
RABBITMQ_PASSWORD=password
```

## Common Commands

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Scale workers
docker-compose up -d --scale worker=5

# Stop services
docker-compose down

# Remove volumes (careful!)
docker-compose down -v

# Run database migrations
docker-compose run --rm api alembic upgrade head

# Access services
# - API: http://localhost:8000
# - Flower: http://localhost:5555 (or 5556 with custom ports)
# - RabbitMQ Management: http://localhost:15672 (when using Celery alternative)
# - Adminer: http://localhost:8080 (development only)
# - MailHog: http://localhost:8025 (development only)
```

## Best Practices

1. **Development**: Use the default `docker-compose.yml` with automatic `docker-compose.override.yml`
2. **Testing**: Use `docker/development/docker-compose.simple.yml` for isolated testing
3. **Production**: Combine base with `docker/production/docker-compose.prod.yml`
4. **Port Conflicts**: Use `docker/development/docker-compose.custom.yml` to remap ports

## Notes

- The main `docker-compose.yml` includes health checks and proper dependencies
- Worker replicas are configured for horizontal scaling
- All services use the `evergreen-network` bridge network
- Persistent data is stored in named volumes
- Logs are configured with size limits to prevent disk exhaustion