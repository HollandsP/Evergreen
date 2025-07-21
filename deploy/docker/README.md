# Docker Setup Guide

This guide provides comprehensive instructions for running the AI Content Generation Pipeline using Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- 16GB RAM (minimum)
- 20GB free disk space

## Quick Start

1. **Clone the repository and navigate to the project**:
   ```bash
   cd /path/to/evergreen
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Build and start services**:
   ```bash
   make quick-start
   ```

This will build images, run migrations, and start all services.

## Architecture

The Docker setup includes the following services:

- **API**: FastAPI application server
- **Worker**: Celery workers for async processing
- **Beat**: Celery beat scheduler for periodic tasks
- **Database**: PostgreSQL 14 for data persistence
- **Redis**: Cache and message broker
- **Flower**: Celery monitoring dashboard
- **Nginx**: Reverse proxy (production only)

## Development Usage

### Starting Services

```bash
# Build and start all services
make up

# Or manually with docker-compose
docker-compose up -d
```

Services will be available at:
- API: http://localhost:8000
- Flower: http://localhost:5555
- Database: localhost:5432
- Redis: localhost:6379

### Managing Services

```bash
# View logs
make logs           # All services
make logs-api       # API only
make logs-worker    # Workers only

# Access containers
make shell          # API shell
make shell-worker   # Worker shell
make db-shell       # PostgreSQL shell

# Check status
make ps             # Container status
make health         # Health checks
make stats          # Resource usage
```

### Database Operations

```bash
# Run migrations
make migrate

# Create new migration
make migrate-create MESSAGE="Add new table"

# Backup database
make db-backup

# Restore database
make db-restore FILE=backups/backup_20240101_120000.sql.gz
```

### Development Tools

```bash
# Start additional dev tools
make dev-tools
```

This starts:
- **Adminer**: Database GUI at http://localhost:8080
- **MailHog**: Email testing at http://localhost:8025

## Production Deployment

### Building for Production

```bash
# Build production image
make prod-build VERSION=1.0.0

# Or manually
docker build -t evergreen-pipeline:1.0.0 .
```

### Running in Production

1. **Create production environment file**:
   ```bash
   cp .env.example .env.prod
   # Edit with production values
   ```

2. **Create Docker secrets**:
   ```bash
   echo "strong_password" | docker secret create db_password -
   ```

3. **Start production services**:
   ```bash
   make prod-up
   
   # Or with specific compose file
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

### Production Features

- Multi-stage builds for smaller images
- Non-root user execution
- Health checks on all services
- Resource limits and reservations
- Automatic restart policies
- Log rotation
- SSL/TLS support via Nginx

## Configuration

### Environment Variables

Key environment variables:

```bash
# Application
APP_ENV=production
DEBUG=false

# Database
DATABASE_URL=postgresql://user:pass@db:5432/dbname
DB_PASSWORD=secure_password

# Redis
REDIS_URL=redis://redis:6379

# API Keys
ELEVENLABS_API_KEY=your_key
RUNWAY_API_KEY=your_key
OPENAI_API_KEY=your_key

# AWS
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_REGION=us-east-1
S3_BUCKET=your-bucket

# Monitoring
FLOWER_USER=admin
FLOWER_PASSWORD=secure_password
```

### Resource Limits

Default resource allocations:

| Service | CPU Limit | Memory Limit | CPU Reserved | Memory Reserved |
|---------|-----------|--------------|--------------|-----------------|
| API     | 1 core    | 2GB          | 0.5 cores    | 1GB             |
| Worker  | 2 cores   | 4GB          | 1 core       | 2GB             |
| DB      | 2 cores   | 4GB          | 1 core       | 2GB             |
| Redis   | 1 core    | 2GB          | 0.5 cores    | 1GB             |

Adjust in `docker-compose.prod.yml` as needed.

## Troubleshooting

### Common Issues

1. **Port conflicts**:
   ```bash
   # Check what's using ports
   lsof -i :8000
   lsof -i :5432
   
   # Change ports in docker-compose.yml or .env
   ```

2. **Permission errors**:
   ```bash
   # Fix output directory permissions
   sudo chown -R $(id -u):$(id -g) output/
   ```

3. **Out of memory**:
   ```bash
   # Increase Docker memory limit
   # Docker Desktop: Settings > Resources > Memory
   
   # Or reduce worker concurrency
   # Edit docker-compose.yml worker command
   ```

4. **Database connection errors**:
   ```bash
   # Check database is running
   make health
   
   # Check logs
   make logs-db
   
   # Restart database
   docker-compose restart db
   ```

### Debugging

1. **Enable debug mode**:
   ```bash
   # In .env or docker-compose.override.yml
   DEBUG=true
   ```

2. **Interactive debugging**:
   ```bash
   # Start API with interactive shell
   docker-compose run --rm api python
   
   # Or attach to running container
   docker attach evergreen-api
   ```

3. **View detailed logs**:
   ```bash
   # Follow logs with timestamps
   docker-compose logs -f --timestamps api
   
   # Export logs
   docker-compose logs > logs.txt
   ```

## Maintenance

### Regular Tasks

1. **Database backups** (recommended daily):
   ```bash
   make db-backup
   ```

2. **Clean up old containers and images**:
   ```bash
   make clean-docker
   ```

3. **Update dependencies**:
   ```bash
   # Rebuild with latest packages
   make build --no-cache
   ```

### Monitoring

1. **Check service health**:
   ```bash
   make health
   ```

2. **Monitor resources**:
   ```bash
   make stats
   ```

3. **View Celery tasks**:
   ```bash
   make monitor  # Opens Flower UI
   ```

## Security Best Practices

1. **Use secrets for sensitive data**:
   ```bash
   docker secret create api_key secret.txt
   ```

2. **Run as non-root user** (already configured)

3. **Keep images updated**:
   ```bash
   docker-compose pull
   make build
   ```

4. **Use read-only volumes** where possible

5. **Enable firewall rules** for production

6. **Regular security scans**:
   ```bash
   docker scan evergreen-pipeline:latest
   ```

## Advanced Usage

### Scaling Workers

```bash
# Scale to 5 workers
docker-compose up -d --scale worker=5

# Or in docker-compose.yml
# deploy:
#   replicas: 5
```

### Custom Networks

The setup uses a custom bridge network for isolation:
```yaml
networks:
  evergreen-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Volume Management

```bash
# List volumes
docker volume ls | grep evergreen

# Backup volumes
docker run --rm -v evergreen_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-backup.tar.gz -C /data .

# Clean unused volumes
docker volume prune
```

## Support

For issues or questions:
1. Check logs: `make logs`
2. Review this guide
3. Check project documentation
4. Open an issue on GitHub