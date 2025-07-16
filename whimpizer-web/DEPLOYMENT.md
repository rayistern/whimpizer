# Whimpizer Web Deployment Guide

## 🚀 Production Deployment Architecture

**Frontend**: Netlify (React/Vite SPA)  
**Backend**: Render or Railway (FastAPI + Redis)  
**AI Provider**: Portkey Gateway  
**Database**: Redis (file-based storage for jobs)

---

## 📱 Frontend Deployment (Netlify)

### 1. Prepare Frontend for Deployment

```bash
cd frontend
npm run build
```

### 2. Deploy to Netlify

**Option A: Git Integration (Recommended)**
1. Push your code to GitHub
2. Connect Netlify to your repository
3. Configure build settings:
   - Build command: `npm run build`
   - Publish directory: `dist`
   - Environment variables: `VITE_API_URL=https://your-backend-url.com`

**Option B: Manual Deploy**
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

### 3. Configure Environment Variables

In Netlify dashboard → Site settings → Environment variables:
```
VITE_API_URL=https://your-backend-domain.render.com
```

---

## 🖥️ Backend Deployment (Render)

### 1. Prepare Backend for Production

Update `whimpizer-web/.env`:
```bash
# Production settings
ENVIRONMENT=production
DEBUG=false
REDIS_URL=redis://your-redis-instance:6379

# AI Configuration
AI_API_KEY=your_portkey_api_key
AI_BASE_URL=https://api.portkey.ai/v1

# CORS - Add your Netlify domain
ALLOWED_HOSTS=["https://your-app-name.netlify.app"]
```

### 2. Deploy to Render

**Create new Web Service:**
1. Connect your GitHub repository
2. Configure service:
   - Name: `whimpizer-backend`
   - Environment: `Docker`
   - Build Command: `docker build -t whimpizer-backend ./backend`
   - Start Command: `docker run -p $PORT:8000 whimpizer-backend`

**Or use direct Python deployment:**
- Root Directory: `backend`
- Build Command: `pip install -r requirements.txt`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 3. Add Redis Database

**Option A: Render Redis (Recommended)**
1. Create Redis instance on Render
2. Copy connection URL to environment variables

**Option B: External Redis (RedisLabs/Upstash)**
```bash
REDIS_URL=redis://username:password@host:port
```

### 4. Environment Variables in Render

```bash
ENVIRONMENT=production
DEBUG=false
REDIS_URL=redis://...
AI_API_KEY=pk_live_...
AI_BASE_URL=https://api.portkey.ai/v1
ALLOWED_HOSTS=["https://your-app.netlify.app"]
WHIMPIZER_CONFIG_PATH=/app/whimpizer_config/config.yaml
WHIMPIZER_SRC_PATH=/app/whimpizer_src
WHIMPIZER_RESOURCES_PATH=/app/whimpizer_resources
```

---

## 🔧 Alternative Backend Deployment (Railway)

### Quick Deploy to Railway

```bash
npm install -g @railway/cli
railway login
railway link
railway up
```

### Railway Configuration

Create `railway.toml`:
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "backend/Dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
```

---

## 🛠️ Local Development Setup

### 1. Backend Setup

```bash
cd whimpizer-web
cp .env.example .env
# Edit .env with your API keys

# Start with Docker
docker-compose up -d

# Or start manually
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 2. Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env
# Edit .env with backend URL

npm run dev
```

### 3. Test Full Stack

- Frontend: http://localhost:3001
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

---

## 🔐 Environment Variables Reference

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000  # Development
# VITE_API_URL=https://your-backend.render.com  # Production
```

### Backend (.env)
```bash
# Core
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# AI Provider (Portkey)
AI_API_KEY=pk_live_your_portkey_key
AI_BASE_URL=https://api.portkey.ai/v1
PORTKEY_APP_ID=your_app_id  # Optional

# Database
REDIS_URL=redis://localhost:6379

# CORS
ALLOWED_HOSTS=["http://localhost:3001","https://your-app.netlify.app"]

# File paths (for Docker deployment)
WHIMPIZER_CONFIG_PATH=/app/whimpizer_config/config.yaml
WHIMPIZER_SRC_PATH=/app/whimpizer_src
WHIMPIZER_RESOURCES_PATH=/app/whimpizer_resources
```

---

## 📋 Pre-Deployment Checklist

### Frontend
- [ ] Build succeeds locally (`npm run build`)
- [ ] Environment variables configured
- [ ] API endpoints tested
- [ ] Netlify configuration verified

### Backend
- [ ] Health check responds (`/health`)
- [ ] AI provider connection tested
- [ ] Redis connection verified
- [ ] Original whimpizer assets mounted
- [ ] CORS origins include frontend domain

### Infrastructure
- [ ] Portkey API key configured and working
- [ ] Redis instance provisioned
- [ ] Domain DNS configured (if custom domain)
- [ ] SSL certificates active

---

## 🚨 Troubleshooting

### Common Issues

**CORS Errors**
```bash
# Add your frontend domain to backend ALLOWED_HOSTS
ALLOWED_HOSTS=["https://your-app.netlify.app"]
```

**API Connection Failed**
```bash
# Check backend health endpoint
curl https://your-backend.render.com/health

# Verify frontend environment variable
echo $VITE_API_URL
```

**Redis Connection Issues**
```bash
# Test Redis connection
redis-cli -u $REDIS_URL ping
```

**Portkey AI Errors**
```bash
# Test Portkey connection
curl -X POST "https://your-backend.render.com/api/providers/openai/test"
```

### Logs and Monitoring

**Backend Logs (Render)**
```bash
render logs --service=whimpizer-backend --tail
```

**Frontend Logs (Netlify)**
- Check deploy logs in Netlify dashboard
- Use browser dev tools for runtime errors

---

## 📈 Scaling Considerations

### Performance Optimization
- Use CDN for static assets (Netlify handles this)
- Implement job queue cleanup (Redis memory management)
- Add caching for provider info API calls
- Consider job result compression

### Future Enhancements
- Add user authentication (Auth0/Supabase Auth)
- Implement persistent storage (Supabase Database)
- Add job result sharing features
- Implement batch processing

---

## 💰 Cost Estimation

### Free Tier Deployment
- **Netlify**: Free (100GB bandwidth, 300 build minutes)
- **Render**: Free tier (750 hours, sleeps after 15min inactivity)
- **Portkey**: Pay-per-use (starts free)
- **Total**: ~$0-10/month for light usage

### Production Tier
- **Netlify Pro**: $19/month
- **Render Standard**: $25/month  
- **Redis**: $15/month
- **Portkey**: Usage-based
- **Total**: ~$60-100/month for serious usage

Happy deploying! 🚀