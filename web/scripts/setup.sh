#!/bin/bash

# Evergreen AI Web Interface Setup Script
set -e

echo "🚀 Setting up Evergreen AI Web Interface..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    print_error "Node.js version 18 or higher is required. Current version: $(node --version)"
    exit 1
fi

print_success "Node.js $(node --version) detected"

# Check if we're in the web directory
if [ ! -f "package.json" ]; then
    print_error "This script must be run from the web directory"
    exit 1
fi

# Install dependencies
print_status "Installing dependencies..."
if command -v yarn &> /dev/null; then
    yarn install
else
    npm install
fi
print_success "Dependencies installed"

# Copy environment file if it doesn't exist
if [ ! -f ".env.local" ]; then
    print_status "Creating environment configuration..."
    cp .env.example .env.local
    print_warning "Please edit .env.local with your configuration"
    print_warning "Set BACKEND_URL to point to your running backend service"
else
    print_status "Environment file already exists"
fi

# Check if backend is running
print_status "Checking backend connectivity..."
BACKEND_URL=${BACKEND_URL:-"http://localhost:8000"}
if curl -f -s "${BACKEND_URL}/health" > /dev/null 2>&1; then
    print_success "Backend is accessible at ${BACKEND_URL}"
else
    print_warning "Backend is not accessible at ${BACKEND_URL}"
    print_warning "Make sure your backend service is running before starting the web interface"
fi

# Build the application
print_status "Building the application..."
if command -v yarn &> /dev/null; then
    yarn build
else
    npm run build
fi
print_success "Application built successfully"

# Final instructions
echo ""
print_success "Setup complete! 🎉"
echo ""
echo "Next steps:"
echo "1. Edit .env.local with your backend configuration"
echo "2. Ensure your backend service is running"
echo "3. Start the development server:"
if command -v yarn &> /dev/null; then
    echo "   yarn dev"
else
    echo "   npm run dev"
fi
echo ""
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "For production deployment:"
if command -v yarn &> /dev/null; then
    echo "   yarn start"
else
    echo "   npm start"
fi
echo ""
print_status "Happy generating! ✨"