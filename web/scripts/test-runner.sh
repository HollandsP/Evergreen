#!/bin/bash

# Test runner script for comprehensive test execution
# Usage: ./scripts/test-runner.sh [type] [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

cleanup() {
    log_info "Cleaning up test environment..."
    npm run test:docker:clean > /dev/null 2>&1 || true
}

# Trap cleanup on exit
trap cleanup EXIT

# Default values
TEST_TYPE="${1:-all}"
COVERAGE="${2:-true}"
PARALLEL="${3:-true}"

log_info "Starting test runner - Type: $TEST_TYPE, Coverage: $COVERAGE, Parallel: $PARALLEL"

# Pre-test checks
log_info "Running pre-test checks..."

# Check if dependencies are installed
if [ ! -d "node_modules" ]; then
    log_warning "Node modules not found, installing..."
    npm install
fi

# Check if Docker is available for integration tests
if ! command -v docker &> /dev/null; then
    log_warning "Docker not found - integration tests with containers will be skipped"
    DOCKER_AVAILABLE=false
else
    DOCKER_AVAILABLE=true
fi

# Test execution based on type
case $TEST_TYPE in
    "unit")
        log_info "Running unit tests..."
        if [ "$COVERAGE" = "true" ]; then
            npm run test:unit -- --coverage
        else
            npm run test:unit
        fi
        ;;
    
    "integration")
        log_info "Running integration tests..."
        npm run test:integration
        ;;
    
    "api")
        log_info "Running API tests..."
        npm run test:api
        ;;
    
    "docker")
        if [ "$DOCKER_AVAILABLE" = "true" ]; then
            log_info "Running tests in Docker environment..."
            npm run test:docker
        else
            log_error "Docker not available for containerized tests"
            exit 1
        fi
        ;;
    
    "ci")
        log_info "Running CI test suite..."
        npm run test:ci
        ;;
    
    "all")
        log_info "Running comprehensive test suite..."
        
        # Unit tests first (fastest)
        log_info "1/4 Running unit tests..."
        npm run test:unit
        
        # API tests
        log_info "2/4 Running API tests..."
        npm run test:api
        
        # Integration tests
        log_info "3/4 Running integration tests..."
        npm run test:integration
        
        # Full coverage report
        log_info "4/4 Generating coverage report..."
        if [ "$COVERAGE" = "true" ]; then
            npm run test:coverage
        fi
        ;;
    
    "quick")
        log_info "Running quick test suite (no coverage)..."
        npm test -- --passWithNoTests --silent
        ;;
    
    *)
        log_error "Unknown test type: $TEST_TYPE"
        echo "Available types: unit, integration, api, docker, ci, all, quick"
        exit 1
        ;;
esac

# Test results analysis
if [ $? -eq 0 ]; then
    log_success "All tests completed successfully!"
    
    # Show coverage summary if available
    if [ -f "coverage/lcov-report/index.html" ]; then
        log_info "Coverage report generated: coverage/lcov-report/index.html"
    fi
    
    # Show performance metrics
    if [ -f ".test-results.json" ]; then
        log_info "Performance metrics available in .test-results.json"
    fi
    
else
    log_error "Some tests failed. Check output above for details."
    exit 1
fi