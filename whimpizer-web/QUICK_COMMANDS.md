# 🚀 Quick Commands Reference

## 🐳 **Starting Services**

```bash
# Interactive mode (see logs in terminal)
./start-dev.sh

# Background mode (services run in background)
./start-dev-background.sh

# Manual start (if scripts don't work)
docker compose -f docker-compose.dev.yml up --build
```

## 🔍 **Monitoring & Debugging**

```bash
# View all service status
docker compose -f docker-compose.dev.yml ps

# View logs for all services
docker compose -f docker-compose.dev.yml logs -f

# View logs for specific service
docker compose -f docker-compose.dev.yml logs -f backend
docker compose -f docker-compose.dev.yml logs -f frontend
docker compose -f docker-compose.dev.yml logs -f portkey
docker compose -f docker-compose.dev.yml logs -f redis

# Check service health
curl http://localhost:8000/health         # Backend
curl http://localhost:8787/health         # Portkey
```

## 🛠️ **Managing Services**

```bash
# Stop all services
docker compose -f docker-compose.dev.yml down

# Restart all services
docker compose -f docker-compose.dev.yml restart

# Restart specific service
docker compose -f docker-compose.dev.yml restart backend

# Rebuild and restart (after code changes)
docker compose -f docker-compose.dev.yml up --build

# Force rebuild (clean build)
docker compose -f docker-compose.dev.yml build --no-cache
```

## 🧹 **Cleanup**

```bash
# Stop and remove containers + networks
docker compose -f docker-compose.dev.yml down

# Remove containers + volumes (⚠️ deletes data)
docker compose -f docker-compose.dev.yml down -v

# Remove everything + images
docker compose -f docker-compose.dev.yml down --rmi all -v

# Clean up Docker system
docker system prune
```

## 🔧 **Development Shortcuts**

```bash
# Rebuild just the backend
docker compose -f docker-compose.dev.yml build backend
docker compose -f docker-compose.dev.yml restart backend

# Rebuild just the frontend  
docker compose -f docker-compose.dev.yml build frontend
docker compose -f docker-compose.dev.yml restart frontend

# Execute commands in running containers
docker compose -f docker-compose.dev.yml exec backend bash
docker compose -f docker-compose.dev.yml exec frontend sh
```

## 🌐 **Access URLs**

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:3001 | React app |
| **Backend API** | http://localhost:8000 | FastAPI server |
| **API Docs** | http://localhost:8000/docs | Swagger documentation |
| **Portkey Gateway** | http://localhost:8787 | AI provider proxy |
| **Redis** | localhost:6379 | Job queue & cache |

## 🐛 **Quick Fixes**

```bash
# "Command not found" errors
chmod +x start-dev.sh
chmod +x start-dev-background.sh

# Port already in use
sudo lsof -i :3001    # Find what's using port 3001
sudo lsof -i :8000    # Find what's using port 8000

# Permission denied
sudo chown -R $USER:$USER .

# API keys not working
grep API_KEY .env     # Check if keys are set
```

## 📊 **Testing & Validation**

```bash
# Test backend API
curl http://localhost:8000/health
curl http://localhost:8000/api/jobs

# Test Portkey connection
curl http://localhost:8787/health

# Test Redis connection
redis-cli -h localhost -p 6379 ping

# Run backend tests (if added)
docker compose -f docker-compose.dev.yml exec backend pytest

# Check frontend build
docker compose -f docker-compose.dev.yml exec frontend npm run build
```

## ⚡ **One-Liners**

```bash
# Quick restart everything
docker compose -f docker-compose.dev.yml restart && echo "✅ All services restarted!"

# Check if everything is running
docker compose -f docker-compose.dev.yml ps | grep -E "(Up|running)"

# Follow logs for main services
docker compose -f docker-compose.dev.yml logs -f backend frontend

# Emergency stop and clean restart
docker compose -f docker-compose.dev.yml down && docker compose -f docker-compose.dev.yml up --build -d
```

## 🆘 **Emergency Commands**

```bash
# If everything is broken
docker compose -f docker-compose.dev.yml down -v
docker system prune -f
./start-dev.sh

# If Docker is acting weird
docker system df          # Check disk usage
docker system prune -a     # Clean everything
sudo systemctl restart docker  # Restart Docker daemon
```

---

**💡 Tip**: Bookmark this file! These commands will save you tons of time during development.