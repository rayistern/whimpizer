# Whimpizer Web Frontend

A modern web interface for the Whimpizer content-to-Wimpy-Kid pipeline.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- AI API key (Portkey or OpenRouter)

### Setup

1. **Clone and navigate to web directory**:
```bash
cd whimpizer-web
```

2. **Set up environment**:
```bash
cp .env.example .env
# Edit .env with your AI API key
```

3. **Start the stack**:
```bash
docker-compose up -d
```

4. **Access the application**:
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs
- Frontend: http://localhost:3001

## 🏗️ Architecture

```
whimpizer-web/
├── backend/                 # FastAPI server
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   │   ├── jobs.py     # Job management endpoints
│   │   │   └── providers.py # AI provider info
│   │   ├── core/           # Configuration
│   │   │   └── config.py   # Settings and environment
│   │   ├── models/         # Pydantic models
│   │   │   └── jobs.py     # Job-related data models
│   │   ├── services/       # Business logic
│   │   │   ├── job_manager.py      # Job state management
│   │   │   └── whimpizer_service.py # Pipeline wrapper
│   │   └── main.py         # FastAPI app
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # React app (Phase 3)
├── docker-compose.yml      # Full stack orchestration
├── .env.example           # Environment template
└── README.md              # This file
```

## 🔧 API Endpoints

### Jobs Management
- `POST /api/jobs` - Submit new whimpizer job
- `GET /api/jobs/{job_id}/status` - Check job status
- `GET /api/jobs` - List all jobs (paginated)
- `GET /api/jobs/{job_id}/download` - Download completed PDF
- `DELETE /api/jobs/{job_id}` - Cancel/delete job

### Providers
- `GET /api/providers` - List available AI providers
- `GET /api/providers/{provider_name}` - Get provider details

## 📋 Job Workflow

1. **Submit URLs** → Returns job ID
2. **Polling Status** → Check progress (downloading → processing → generating PDF)
3. **Download PDF** → When status = "completed"

## 🛠️ Development

### Backend Only
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### With Redis
```bash
docker run -d -p 6379:6379 redis:alpine
cd backend
python -m uvicorn app.main:app --reload
```

### Full Stack
```bash
docker-compose up --build
```

## 📊 Job States

| Status | Description |
|--------|-------------|
| `pending` | Job submitted, waiting to start |
| `downloading` | Downloading web content |
| `processing` | AI processing content |
| `generating_pdf` | Creating final PDF |
| `completed` | Job finished, PDF ready |
| `failed` | Job failed, check error message |
| `cancelled` | Job cancelled by user |

## 🔑 Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `AI_API_KEY` | Portkey/OpenRouter API key | `pk-xxx` or `sk-or-xxx` |
| `AI_BASE_URL` | AI provider base URL | `https://api.portkey.ai/v1` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `DEBUG` | Enable debug mode | `true` |

## 🎯 Current Status

✅ **Phase 1 Complete**: Backend API Foundation
- FastAPI server with job management
- Redis-based job queue
- Wrapped existing whimpizer pipeline
- Docker containerization

🔄 **Phase 2 Next**: AI Integration & Job Processing
- Portkey/OpenRouter integration
- Background job processing
- File handling improvements

📋 **Phase 3 Planned**: React Frontend
- Modern UI with Wimpy Kid theme
- Job submission and status tracking
- Responsive design

## 🧪 Testing

```bash
# Test the API
curl -X POST "http://localhost:8000/api/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "config": {
      "ai_provider": "openai",
      "ai_model": "gpt-4"
    }
  }'

# Check job status
curl "http://localhost:8000/api/jobs/{job_id}/status"
```

## 🚨 Troubleshooting

**Redis connection issues**:
```bash
docker-compose logs redis
```

**Backend errors**:
```bash
docker-compose logs backend
```

**Check API health**:
```bash
curl http://localhost:8000/health
```

## 📝 Next Steps

1. Test backend API endpoints
2. Integrate with AI provider (Portkey/OpenRouter)
3. Begin React frontend development
4. Add user authentication (optional)
5. Deploy to production