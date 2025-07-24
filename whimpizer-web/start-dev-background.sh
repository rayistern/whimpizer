#!/bin/bash

# Background Development Environment Startup Script

echo "🚀 Starting Whimpizer Development Environment (Background Mode)..."

# Check if .env exists, if not copy from .env.dev
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.dev template..."
    cp .env.dev .env
    echo "⚠️  Please edit .env and add your actual API keys!"
    echo "   Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY"
    echo ""
fi

# Start all services in background
echo "🐳 Starting Docker containers in background..."

# Try modern Docker Compose command first, fallback to legacy
if command -v docker &> /dev/null; then
    if docker compose version &> /dev/null; then
        echo "Using: docker compose"
        docker compose -f docker-compose.dev.yml up --build -d
        DOCKER_CMD="docker compose"
    elif docker-compose --version &> /dev/null; then
        echo "Using: docker-compose (legacy)"
        docker-compose -f docker-compose.dev.yml up --build -d
        DOCKER_CMD="docker-compose"
    else
        echo "❌ Error: Neither 'docker compose' nor 'docker-compose' found!"
        echo "Please install Docker and Docker Compose"
        exit 1
    fi
else
    echo "❌ Error: Docker not found! Please install Docker first."
    exit 1
fi

# Wait a moment for containers to start
echo "⏳ Waiting for services to initialize..."
sleep 3

# Check if services are running
echo "🔍 Checking service status..."
if command -v docker &> /dev/null; then
    if [[ $DOCKER_CMD == "docker compose" ]]; then
        docker compose -f docker-compose.dev.yml ps
    else
        docker-compose -f docker-compose.dev.yml ps
    fi
fi

echo ""
echo "✅ All services started in background!"
echo ""
echo "🌐 Access points:"
echo "   Frontend: http://localhost:3001"
echo "   Backend API: http://localhost:8000"
echo "   Portkey Gateway: http://localhost:8787"
echo "   Redis: localhost:6379"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "🔧 Portkey Health: http://localhost:8787/health"
echo ""
echo "🛠️  Useful commands:"
echo "   View logs: $DOCKER_CMD -f docker-compose.dev.yml logs -f"
echo "   Stop all:  $DOCKER_CMD -f docker-compose.dev.yml down"
echo "   Restart:   $DOCKER_CMD -f docker-compose.dev.yml restart"