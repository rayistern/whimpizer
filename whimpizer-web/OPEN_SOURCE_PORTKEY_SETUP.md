# 🚀 Open Source Portkey Setup Guide

This guide shows you how to set up the **open source Portkey gateway** for unified AI provider access with your Whimpizer/Bookerizer application.

## 📋 What You Get

✅ **Unified AI Interface** - Switch between OpenAI, Anthropic, Google without code changes  
✅ **Cost Optimization** - Route to cheapest provider automatically  
✅ **Rate Limiting** - Built-in protection against API limits  
✅ **Request Logging** - Track all AI requests and costs  
✅ **Self-Hosted** - No external dependencies or data sharing  

## 🛠️ Quick Setup (Super Easy!)

### 1. Prerequisites
```bash
# You need Docker installed
docker --version
docker compose --version
```

### 2. Clone and Configure
```bash
cd whimpizer-web

# Copy environment template
cp .env.dev .env

# Edit .env and add your API keys
nano .env
# Add: OPENAI_API_KEY=sk-...
# Add: ANTHROPIC_API_KEY=sk-ant-...
# Add: GOOGLE_API_KEY=...
```

### 3. Start Everything
```bash
# Option 1: Use our startup script
./start-dev.sh

# Option 2: Manual start
docker compose -f docker-compose.dev.yml up --build
```

### 4. Access Your Services
- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://localhost:8000/docs
- ⚡ **Portkey Gateway**: http://localhost:8787
- 📊 **Redis**: localhost:6379

## 🔧 Configuration

### Portkey Gateway Config (`portkey-config/config.yaml`)
```yaml
providers:
  openai:
    api_key: "${OPENAI_API_KEY}"
    base_url: "https://api.openai.com/v1"
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    base_url: "https://api.anthropic.com"
  google:
    api_key: "${GOOGLE_API_KEY}"
    base_url: "https://generativelanguage.googleapis.com"

settings:
  default_provider: "openai"
  timeout: 30
  retries: 3

rate_limits:
  openai:
    requests_per_minute: 60
    tokens_per_minute: 90000
```

### Environment Variables (`.env`)
```bash
# Enable open source mode
USE_OPEN_SOURCE_PORTKEY=true
AI_BASE_URL=http://portkey:8000

# Your API keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

## 📊 Admin Settings (No Database Required!)

### File-Based Configuration
Admin settings are stored in JSON files, no database needed:
- **Location**: `/app/config/admin_settings.json`
- **Backup**: Automatically created
- **Version Control**: Can be committed to git

### Available Settings
```json
{
  "max_concurrent_jobs": 5,
  "max_urls_per_job": 10,
  "default_max_tokens": 3000,
  "rate_limits": {
    "requests_per_minute": 10,
    "requests_per_hour": 100
  },
  "ai_settings": {
    "default_provider": "openai",
    "default_model": "gpt-4o-mini",
    "temperature": 0.7
  },
  "ui_settings": {
    "site_title": "Bookerizer",
    "enable_registration": true,
    "require_auth": false
  }
}
```

## 🎛️ Admin Dashboard (Coming Soon!)

We can add an admin panel with:
- **Live Settings Editor** - Update configuration in real-time
- **Job Monitoring** - See active/queued/completed jobs  
- **Usage Analytics** - Token usage by provider
- **Rate Limit Dashboard** - Monitor API limits
- **Cost Tracking** - Estimate costs per provider

## 🚀 Next Steps

1. **Stripe Integration** - Payment processing & subscription plans
2. **Token Balance System** - User credits and usage tracking  
3. **Landing Page** - Professional marketing site
4. **Static Pages** - Help, Terms, Privacy Policy
5. **Advanced Analytics** - User behavior and conversion tracking

## 🏷️ Branding: "Bookerizer"

Great choice! This allows expansion beyond Wimpy Kid:
- **Domain**: bookerizer.com
- **Tagline**: "Transform any content into illustrated children's stories"
- **Future Books**: Harry Potter style, Dr. Seuss style, etc.

## 🔧 Troubleshooting

### Portkey Not Starting
```bash
# Check logs
docker compose -f docker-compose.dev.yml logs portkey

# Common issue: API keys not set
grep API_KEY .env
```

### Backend Can't Connect to Portkey
```bash
# Test Portkey health
curl http://localhost:8787/health

# Check network connectivity
docker compose -f docker-compose.dev.yml ps
```

### Frontend Build Issues
```bash
# Rebuild frontend
docker compose -f docker-compose.dev.yml build frontend
```

## 📞 Need Help?

The setup is designed to be **super simple** - most issues are just missing API keys. If you get stuck:

1. Check the logs: `docker compose logs`
2. Verify API keys are in `.env`
3. Make sure ports 3000, 8000, 8787, 6379 are free
4. Try restarting: `docker compose down && docker compose up`