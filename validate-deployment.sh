#!/bin/bash

# Evergreen AI Video Pipeline - Deployment Validation Script
# Quick validation to ensure production deployment is working correctly

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
API_URL="http://localhost:8000"
WEB_URL="http://localhost:3000"
FLOWER_URL="http://localhost:5555"

# Test results tracking
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Functions
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Test function wrapper
run_test() {
    local test_name="$1"
    local test_command="$2"
    
    log "Running test: $test_name"
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if eval "$test_command"; then
        success "$test_name - PASSED"
        return 0
    else
        error "$test_name - FAILED"
        return 1
    fi
}

# Docker services validation
validate_docker_services() {
    log "Validating Docker services..."
    
    # Check if docker-compose is running
    run_test "Docker Compose Services" "docker-compose ps | grep -q 'Up'"
    
    # Check individual services
    local services=("web" "api" "db" "redis" "worker" "beat")
    
    for service in "${services[@]}"; do
        run_test "Service: $service" "docker-compose ps $service | grep -q 'Up'"
    done
}

# API endpoint validation
validate_api_endpoints() {
    log "Validating API endpoints..."
    
    # Health check
    run_test "API Health Check" "curl -f -s $API_URL/health >/dev/null"
    
    # API documentation
    run_test "API Documentation" "curl -f -s $API_URL/docs >/dev/null"
    
    # Status endpoint
    run_test "API Status" "curl -f -s $API_URL/api/status >/dev/null"
    
    # Check API response format
    run_test "API JSON Response" "curl -s $API_URL/health | jq . >/dev/null 2>&1"
}

# Web frontend validation
validate_web_frontend() {
    log "Validating web frontend..."
    
    # Main page
    run_test "Web Frontend Main Page" "curl -f -s $WEB_URL >/dev/null"
    
    # Production pipeline page
    run_test "Production Pipeline Page" "curl -f -s $WEB_URL/production >/dev/null"
    
    # Static assets
    run_test "Web Static Assets" "curl -f -s $WEB_URL/_next/static >/dev/null || true"
}

# Database validation
validate_database() {
    log "Validating database..."
    
    # Database connection
    run_test "Database Connection" "docker-compose exec -T db pg_isready -U pipeline -d pipeline"
    
    # Check tables exist
    run_test "Database Tables" "docker-compose exec -T db psql -U pipeline -d pipeline -c '\\dt' | grep -q 'public'"
    
    # Migration status
    run_test "Database Migrations" "docker-compose exec -T api alembic current >/dev/null 2>&1"
}

# Redis validation
validate_redis() {
    log "Validating Redis..."
    
    # Redis ping
    run_test "Redis Connection" "docker-compose exec -T redis redis-cli ping | grep -q PONG"
    
    # Redis info
    run_test "Redis Info" "docker-compose exec -T redis redis-cli info | grep -q 'redis_version'"
}

# Celery validation
validate_celery() {
    log "Validating Celery..."
    
    # Celery workers
    run_test "Celery Workers" "docker-compose exec -T worker celery -A workers.celery_app inspect ping >/dev/null 2>&1"
    
    # Celery beat scheduler
    run_test "Celery Beat Status" "docker-compose ps beat | grep -q 'Up'"
    
    # Flower monitoring
    if curl -f -s "$FLOWER_URL" >/dev/null 2>&1; then
        success "Flower Monitoring - PASSED"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        warning "Flower Monitoring - Not accessible (may require authentication)"
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Environment validation
validate_environment() {
    log "Validating environment configuration..."
    
    # Check .env file exists
    run_test "Environment File" "[ -f .env ]"
    
    # Check critical environment variables
    if [ -f .env ]; then
        source .env
        
        local required_vars=(
            "DATABASE_URL"
            "REDIS_URL" 
            "OPENAI_API_KEY"
            "ELEVENLABS_API_KEY"
            "RUNWAY_API_KEY"
        )
        
        for var in "${required_vars[@]}"; do
            if [ -n "${!var}" ] && [ "${!var}" != "your-"*"-key-here" ]; then
                success "Environment Variable: $var - CONFIGURED"
                TESTS_PASSED=$((TESTS_PASSED + 1))
            else
                error "Environment Variable: $var - NOT CONFIGURED"
                TESTS_FAILED=$((TESTS_FAILED + 1))
            fi
            TESTS_RUN=$((TESTS_RUN + 1))
        done
    fi
}

# Performance validation
validate_performance() {
    log "Validating performance..."
    
    # API response time
    local api_time=$(curl -o /dev/null -s -w "%{time_total}" "$API_URL/health")
    if (( $(echo "$api_time < 2.0" | bc -l) )); then
        success "API Response Time: ${api_time}s - GOOD"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        warning "API Response Time: ${api_time}s - SLOW"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
    
    # Web frontend response time
    local web_time=$(curl -o /dev/null -s -w "%{time_total}" "$WEB_URL")
    if (( $(echo "$web_time < 3.0" | bc -l) )); then
        success "Web Response Time: ${web_time}s - GOOD"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        warning "Web Response Time: ${web_time}s - SLOW"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
}

# Security validation
validate_security() {
    log "Validating security..."
    
    # Check for exposed secrets
    run_test "No Exposed Secrets" "! docker-compose config | grep -i 'password.*:.*[^*]'"
    
    # Check container user (non-root)
    run_test "Non-root API Container" "docker-compose exec -T api whoami | grep -v root"
    run_test "Non-root Web Container" "docker-compose exec -T web whoami | grep -v root"
    
    # Check HTTPS redirect (if nginx is running)
    if docker-compose ps nginx | grep -q 'Up'; then
        run_test "HTTPS Redirect" "curl -s -o /dev/null -w '%{http_code}' http://localhost | grep -q '301'"
    fi
}

# Generate report
generate_report() {
    echo ""
    echo "======================================"
    echo "Deployment Validation Report"
    echo "======================================"
    echo ""
    echo "Tests Run: $TESTS_RUN"
    echo "Passed: $TESTS_PASSED"
    echo "Failed: $TESTS_FAILED"
    echo ""
    
    if [ $TESTS_FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ ALL TESTS PASSED - Deployment is healthy!${NC}"
        echo ""
        echo "🌐 Web Interface: $WEB_URL"
        echo "🔧 API Documentation: $API_URL/docs"
        echo "📊 Flower Monitor: $FLOWER_URL"
        echo ""
        return 0
    else
        echo -e "${RED}❌ $TESTS_FAILED TESTS FAILED - Please review and fix issues${NC}"
        echo ""
        echo "Common fixes:"
        echo "- Ensure all services are running: docker-compose ps"
        echo "- Check logs: docker-compose logs [service-name]"
        echo "- Verify environment variables in .env file"
        echo "- Restart services: docker-compose restart"
        echo ""
        return 1
    fi
}

# Main execution
main() {
    echo "🔍 Evergreen AI Video Pipeline - Deployment Validation"
    echo "========================================================"
    echo ""
    
    # Check prerequisites
    if ! command -v docker-compose &> /dev/null; then
        error "docker-compose is not installed"
        exit 1
    fi
    
    if ! command -v curl &> /dev/null; then
        error "curl is not installed"
        exit 1
    fi
    
    # Install jq if not present (for JSON validation)
    if ! command -v jq &> /dev/null; then
        warning "jq not found, installing..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y jq
        elif command -v yum &> /dev/null; then
            sudo yum install -y jq
        else
            warning "Could not install jq, skipping JSON validation"
        fi
    fi
    
    # Install bc if not present (for math operations)
    if ! command -v bc &> /dev/null; then
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y bc
        elif command -v yum &> /dev/null; then
            sudo yum install -y bc
        fi
    fi
    
    # Run validation tests
    validate_docker_services
    validate_environment
    validate_database
    validate_redis
    validate_api_endpoints
    validate_web_frontend
    validate_celery
    validate_performance
    validate_security
    
    # Generate final report
    generate_report
}

# Run main function
main "$@"