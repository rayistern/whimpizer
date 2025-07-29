#!/bin/bash

# Development Environment Startup Script for Open Source Portkey + Whimpizer

echo "🚀 Starting Whimpizer Development Environment with Open Source Portkey..."

# Check if .env exists, if not copy from .env.dev
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.dev template..."
    cp .env.dev .env
    echo "⚠️  Please edit .env and add your actual API keys!"
    echo "   Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY"
    echo ""
fi

# Start all services
echo "🐳 Starting Docker containers..."

# Try modern Docker Compose command first, fallback to legacy
if command -v docker &> /dev/null; then
    if docker compose version &> /dev/null; then
        echo "Using: docker compose"
        docker compose -f docker-compose.dev.yml up --build
    elif docker-compose --version &> /dev/null; then
        echo "Using: docker-compose (legacy)"
        docker-compose -f docker-compose.dev.yml up --build
    else
        echo "❌ Error: Neither 'docker compose' nor 'docker-compose' found!"
        echo "Please install Docker and Docker Compose"
        exit 1
    fi
else
    echo "❌ Error: Docker not found! Please install Docker first."
    exit 1
fi

# Only show success message if we get here (containers started)
echo ""
echo "✅ All services started!"
echo ""
echo "🌐 Access points:"
echo "   Frontend: http://localhost:3001"
echo "   Backend API: http://localhost:8000"
echo "   Portkey Gateway: http://localhost:8787"
echo "   Redis: localhost:6379"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔧 Portkey Health: http://localhost:8787/health"