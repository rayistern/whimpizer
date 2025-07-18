#!/bin/bash

echo "🔍 Docker Debug Information"
echo "=========================="

echo ""
echo "1. Checking if Docker command exists..."
if command -v docker &> /dev/null; then
    echo "✅ Docker command found at: $(which docker)"
else
    echo "❌ Docker command not found in PATH"
    echo "PATH: $PATH"
fi

echo ""
echo "2. Checking Docker version..."
docker --version 2>&1 || echo "❌ Failed to get Docker version"

echo ""
echo "3. Checking Docker service status..."
sudo systemctl status docker 2>&1 | head -5 || echo "❌ Can't check Docker service (may need sudo)"

echo ""
echo "4. Checking Docker Compose..."
if docker compose version &> /dev/null; then
    echo "✅ Modern 'docker compose' found"
    docker compose version
elif docker-compose --version &> /dev/null; then
    echo "✅ Legacy 'docker-compose' found"  
    docker-compose --version
else
    echo "❌ Neither 'docker compose' nor 'docker-compose' found"
fi

echo ""
echo "5. Checking Docker permissions..."
docker ps 2>&1 || echo "❌ Can't run 'docker ps' (permission issue?)"

echo ""
echo "6. Checking if Docker daemon is running..."
docker info &> /dev/null && echo "✅ Docker daemon is running" || echo "❌ Docker daemon not running"

echo ""
echo "🔧 Quick fixes to try:"
echo "   sudo systemctl start docker     # Start Docker service"
echo "   sudo usermod -aG docker \$USER   # Add user to docker group"
echo "   newgrp docker                   # Apply group changes"
echo "   sudo systemctl enable docker    # Auto-start Docker"