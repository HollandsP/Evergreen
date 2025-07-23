#!/bin/bash

# Evergreen AI Video Pipeline - Production Deployment Script
# This script helps deploy the application to production environment

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups"
LOG_FILE="./deploy.log"

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

# Pre-deployment checks
pre_deploy_checks() {
    log "Starting pre-deployment checks..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker and try again."
    fi
    
    # Check if docker-compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed. Please install it and try again."
    fi
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        error ".env file not found. Please copy .env.example to .env and configure it."
    fi
    
    # Check if docker-compose.yml exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "docker-compose.yml not found."
    fi
    
    # Validate required environment variables
    source "$ENV_FILE"
    
    required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "OPENAI_API_KEY"
        "ELEVENLABS_API_KEY"
        "RUNWAY_API_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            error "Required environment variable $var is not set in .env file"
        fi
    done
    
    success "Pre-deployment checks completed successfully"
}

# Backup existing data
backup_data() {
    log "Creating backup of existing data..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database if container is running
    if docker-compose ps db | grep -q "Up"; then
        log "Backing up database..."
        docker-compose exec -T db pg_dump -U pipeline pipeline > "$BACKUP_DIR/database_backup_$(date +%Y%m%d_%H%M%S).sql"
        success "Database backup created"
    fi
    
    # Backup output directory
    if [ -d "./output" ]; then
        log "Backing up output directory..."
        tar -czf "$BACKUP_DIR/output_backup_$(date +%Y%m%d_%H%M%S).tar.gz" ./output
        success "Output directory backup created"
    fi
    
    success "Backup completed"
}

# Build and deploy
deploy() {
    log "Starting deployment..."
    
    # Pull latest images
    log "Pulling latest images..."
    docker-compose pull
    
    # Build images
    log "Building application images..."
    docker-compose build --no-cache
    
    # Stop existing services
    log "Stopping existing services..."
    docker-compose down
    
    # Start services
    log "Starting services..."
    docker-compose up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    check_health
    
    success "Deployment completed successfully"
}

# Health checks
check_health() {
    log "Performing health checks..."
    
    # Check API health
    for i in {1..30}; do
        if curl -f -s http://localhost:8000/health > /dev/null; then
            success "API service is healthy"
            break
        else
            if [ $i -eq 30 ]; then
                error "API service failed to start properly"
            fi
            log "Waiting for API service to be ready... (attempt $i/30)"
            sleep 10
        fi
    done
    
    # Check web frontend
    for i in {1..30}; do
        if curl -f -s http://localhost:3000 > /dev/null; then
            success "Web frontend is healthy"
            break
        else
            if [ $i -eq 30 ]; then
                error "Web frontend failed to start properly"
            fi
            log "Waiting for web frontend to be ready... (attempt $i/30)"
            sleep 10
        fi
    done
    
    # Check database
    if docker-compose exec -T db pg_isready -U pipeline -d pipeline > /dev/null; then
        success "Database is healthy"
    else
        error "Database is not responding"
    fi
    
    # Check Redis
    if docker-compose exec -T redis redis-cli ping | grep -q PONG; then
        success "Redis is healthy"
    else
        error "Redis is not responding"
    fi
    
    # Check Celery workers
    if docker-compose exec -T worker celery -A workers.celery_app inspect ping > /dev/null; then
        success "Celery workers are healthy"
    else
        warning "Celery workers may not be fully ready yet"
    fi
    
    success "All health checks completed"
}

# Post-deployment tasks
post_deploy() {
    log "Running post-deployment tasks..."
    
    # Run database migrations
    log "Running database migrations..."
    docker-compose exec -T api alembic upgrade head
    
    # Restart workers to ensure they pick up any changes
    log "Restarting Celery workers..."
    docker-compose restart worker
    
    # Display service URLs
    log "Deployment information:"
    echo ""
    echo "🌐 Web Interface: http://localhost:3000"
    echo "🔧 API Documentation: http://localhost:8000/docs"
    echo "📊 Flower (Celery Monitor): http://localhost:5555"
    echo "🗄️  Database: localhost:5432"
    echo "🔄 Redis: localhost:6379"
    echo ""
    
    success "Post-deployment tasks completed"
}

# Rollback function
rollback() {
    warning "Rolling back deployment..."
    
    # Stop current services
    docker-compose down
    
    # Restore from backup if available
    latest_backup=$(ls -t "$BACKUP_DIR"/database_backup_*.sql 2>/dev/null | head -n1)
    if [ -n "$latest_backup" ]; then
        log "Restoring database from backup: $latest_backup"
        # Note: This is a simplified rollback. In production, you'd want more sophisticated rollback procedures
        warning "Manual database restore may be required"
    fi
    
    error "Rollback completed. Please check your configuration and try again."
}

# Main execution
main() {
    echo "🚀 Evergreen AI Video Pipeline - Production Deployment"
    echo "======================================================"
    echo ""
    
    # Parse command line arguments
    case "${1:-deploy}" in
        "deploy")
            pre_deploy_checks
            backup_data
            deploy
            post_deploy
            ;;
        "health")
            check_health
            ;;
        "backup")
            backup_data
            ;;
        "rollback")
            rollback
            ;;
        "logs")
            docker-compose logs -f "${2:-}"
            ;;
        "stop")
            log "Stopping all services..."
            docker-compose down
            success "All services stopped"
            ;;
        "restart")
            log "Restarting all services..."
            docker-compose restart
            success "All services restarted"
            ;;
        *)
            echo "Usage: $0 {deploy|health|backup|rollback|logs|stop|restart}"
            echo ""
            echo "Commands:"
            echo "  deploy   - Full deployment (default)"
            echo "  health   - Check service health"
            echo "  backup   - Create backup of data"
            echo "  rollback - Rollback deployment"
            echo "  logs     - View service logs"
            echo "  stop     - Stop all services"
            echo "  restart  - Restart all services"
            exit 1
            ;;
    esac
}

# Trap errors and provide rollback option
trap 'echo ""; error "Deployment failed. Run $0 rollback to rollback changes."' ERR

# Run main function
main "$@"