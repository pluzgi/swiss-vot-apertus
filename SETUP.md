# Swiss Voting Assistant - Setup Guide

## Step 1: Docker Infrastructure Setup ✅

### Prerequisites

- Docker Desktop installed and running
- Docker Compose V2
- Python 3.10+ (for local development)
- 8GB+ RAM recommended

### Project Structure

```
Swiss-Vot-Apertus/
├── docker-compose.yml          # Multi-service orchestration
├── .env.example                # Environment template
├── .env                        # Your local configuration (create from .env.example)
│
├── backend/
│   ├── Dockerfile              # Backend container
│   ├── requirements.txt        # Python dependencies
│   ├── main.py                 # FastAPI application
│   └── config.py               # Configuration management
│
├── data/
│   └── current_initiatives.json # Voting data (from existing project)
│
└── scripts/                    # Data scraping scripts (existing)
```

### Services Architecture

| Service | Port | Purpose |
|---------|------|---------|
| **OpenWebUI** | 3000 | Frontend chat interface |
| **ChromaDB** | 8001 | Vector database for RAG |
| **FastAPI Backend** | 8000 | API & OpenWebUI Pipeline |
| **PostgreSQL** | 5432 | Relational database (dev) |

---

## Quick Start

### 1. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env and add your Swisscom Apertus API key
# APERTUS_API_KEY=your_actual_key_here
```

### 2. Start All Services

```bash
# Build and start all containers
docker-compose up -d

# View logs
docker-compose logs -f

# Check service status
docker-compose ps
```

### 3. Verify Services

- **OpenWebUI**: http://localhost:3000
- **FastAPI Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **ChromaDB**: http://localhost:8001

### 4. Test Backend API

```bash
# Health check
curl http://localhost:8000/health

# List models
curl http://localhost:8000/v1/models

# Get initiatives (placeholder in Step 1)
curl http://localhost:8000/api/initiatives
```

---

## Docker Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# View logs for specific service
docker-compose logs -f backend

# Access backend container shell
docker-compose exec backend bash

# Reset everything (WARNING: deletes all data)
docker-compose down -v
```

---

## Development Workflow

### Local Backend Development (without Docker)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend locally
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Testing Endpoints

```bash
# Health check
curl http://localhost:8000/health

# OpenAI-compatible chat endpoint
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Was ist Initiative 681?"}
    ]
  }'
```

---

## Current Status (Step 1)

### ✅ Completed

- Docker Compose configuration with 4 services
- FastAPI backend with health check
- OpenWebUI frontend container
- ChromaDB vector store
- PostgreSQL database (local dev)
- Environment configuration
- Basic API structure with placeholders

### 🔜 Next Steps (Step 2)

- Connect to Railway PostgreSQL
- Migrate initiative data to database
- Implement ChromaDB indexing
- Create RAG retrieval pipeline
- Build actual API endpoints

---

## Troubleshooting

### Port Conflicts

If ports are already in use, edit `docker-compose.yml`:

```yaml
# Change port mapping from "HOST:CONTAINER"
ports:
  - "3001:8080"  # OpenWebUI on 3001 instead of 3000
```

### Backend Not Starting

```bash
# Check backend logs
docker-compose logs backend

# Rebuild backend
docker-compose up -d --build backend
```

### ChromaDB Connection Issues

```bash
# Restart ChromaDB
docker-compose restart chromadb

# Check ChromaDB logs
docker-compose logs chromadb
```

### Reset Everything

```bash
# Stop and remove all containers, volumes, networks
docker-compose down -v

# Remove old images
docker-compose rm -f

# Start fresh
docker-compose up -d --build
```

---

## Configuration Reference

### Environment Variables (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `APERTUS_API_KEY` | Swisscom API key | Required |
| `DATABASE_URL` | PostgreSQL connection | Local Docker |
| `CHROMADB_HOST` | ChromaDB hostname | chromadb |
| `LOG_LEVEL` | Logging level | info |
| `ENVIRONMENT` | dev/production | development |

---

## Next: Step 2

Once Step 1 is verified working, proceed to:

1. **Database Migration** - Load initiative data into PostgreSQL
2. **ChromaDB Setup** - Index brochure texts for RAG
3. **API Implementation** - Build actual endpoints
4. **RAG Pipeline** - LangChain integration

See migration plan in main README.md
