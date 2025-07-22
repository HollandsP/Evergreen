#!/bin/bash

# Evergreen Web Application Setup Script

echo "🚀 Setting up Evergreen Web Application..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18.17 or later."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo "❌ Node.js version must be 18.17 or later. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js $(node -v) detected"

# Clean install
echo "🧹 Cleaning previous installations..."
rm -rf node_modules package-lock.json .next

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local from .env.example..."
    cp .env.example .env.local
    echo "⚠️  Please edit .env.local and add your API keys"
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p public/uploads
mkdir -p public/temp

# Run type check
echo "🔍 Running type check..."
npm run type-check || echo "⚠️  TypeScript has some errors that need to be fixed"

# Success message
echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env.local and add your API keys"
echo "2. Run 'npm run dev' to start the development server"
echo "3. Open http://localhost:3000 in your browser"
echo ""
echo "Available commands:"
echo "  npm run dev        - Start development server"
echo "  npm run build      - Build for production"
echo "  npm run start      - Start production server"
echo "  npm run lint       - Run ESLint"
echo "  npm run type-check - Check TypeScript types"
echo "  npm run format     - Format code with Prettier"