#!/bin/bash

# Development Environment Startup Script with Sudo (for permission issues)

echo "🚀 Starting Whimpizer Development Environment with Sudo..."

# Check if .env exists, if not copy from .env.dev
if [ ! -f .env ]; then
    echo "📋 Creating .env from .env.dev template..."
    cp .env.dev .env
    echo "⚠️  Please edit .env and add your actual API keys!"
    echo "   Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY"
    echo ""
fi

# Clean up any failed containers first
echo "🧹 Cleaning up any existing containers..."
sudo docker compose -f docker-compose.dev.yml down 2>/dev/null || true

# Start all services with sudo
echo "🐳 Starting Docker containers with sudo..."
sudo docker compose -f docker-compose.dev.yml up --build -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 5

# Check if services are actually running
echo "🔍 Checking service status..."
if sudo docker compose -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo ""
    echo "✅ Services are running!"
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
    echo "   View logs: sudo docker compose -f docker-compose.dev.yml logs -f"
    echo "   Stop all:  sudo docker compose -f docker-compose.dev.yml down"
    echo "   Restart:   sudo docker compose -f docker-compose.dev.yml restart"
else
    echo ""
    echo "❌ Services failed to start. Checking logs..."
    sudo docker compose -f docker-compose.dev.yml ps
    echo ""
    echo "📋 View detailed logs with:"
    echo "   sudo docker compose -f docker-compose.dev.yml logs"
fi