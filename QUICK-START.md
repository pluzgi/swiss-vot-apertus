# Quick Start Guide - Swiss Voting Assistant

## Prerequisites

- Docker Desktop installed and running
- Swisscom Apertus API key (you'll add this)
- Railway PostgreSQL credentials (you'll add this)

---

## 🚀 Setup Steps

### 1. Configure API Keys & Database

```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env  # or use your preferred editor
```

**Add your credentials in .env:**

```bash
# 1. Swisscom Apertus API Key
SWISS_AI_PLATFORM_API_KEY=paste_your_swisscom_api_key_here

# 2. Railway PostgreSQL Connection
DATABASE_URL=paste_your_railway_postgresql_url_here
# Format: postgresql://user:password@host:port/database
```

**That's it!** The backend will use these credentials automatically.

---

### 2. Start Docker Services

```bash
# Start all containers
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f backend
```

---

### 3. Initialize Database (First Time Only)

```bash
# Migrate voting data from swissvotes.ch scraper to PostgreSQL
python scripts/migrate_data.py

# This will:
# - Connect to your Railway PostgreSQL
# - Create tables
# - Import current initiatives from data/current_votes.json
```

---

### 4. Index Brochure Texts for RAG

```bash
# Generate embeddings and index into ChromaDB
python scripts/index_brochures.py

# This will:
# - Load initiatives from database
# - Extract brochure texts (DE/FR/IT)
# - Generate multilingual embeddings
# - Index into ChromaDB for semantic search
```

---

### 5. Verify Everything Works

```bash
# Health check
curl http://localhost:8000/health

# List all current initiatives (from swissvotes.ch)
curl http://localhost:8000/api/initiatives

# Get details of any initiative (use actual vote_id from above)
curl http://localhost:8000/api/initiatives/<vote_id>

# Test RAG semantic search
curl -X POST http://localhost:8000/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Welche Initiativen gibt es zur Klimapolitik?",
    "language": "de"
  }'
```

---

### 6. Access OpenWebUI

Open browser: **http://localhost:3000**

The chat interface connects to your backend automatically.

---

## 🔑 Where You'll Add Credentials

### 1. Swisscom Apertus API Key

You'll provide this and add it to `.env`:

```bash
SWISS_AI_PLATFORM_API_KEY=<your_api_key>
```

**API Specs:**
- Model: Apertus-70B-Instruct-2509
- Rate limit: 5 req/sec, 100k tokens/min

### 2. Railway PostgreSQL URL

You'll provide the connection string and add it to `.env`:

```bash
DATABASE_URL=postgresql://user:password@host.railway.app:5432/database
```

**Why Railway?**
- Cloud persistence (data survives container restarts)
- Accessible from anywhere
- Production-ready

---

## 📊 Data Flow

```
swissvotes.ch (source)
    ↓
GitHub Actions (weekly scraper)
    ↓
data/current_votes.json (local cache)
    ↓
scripts/migrate_data.py (your command)
    ↓
Railway PostgreSQL (persistent storage)
    ↓
Backend API (serves to OpenWebUI)
```

**Note:** Initiatives are **always current** because:
1. GitHub Actions scrapes swissvotes.ch weekly
2. You run `migrate_data.py` to update your database
3. The scraper only includes **upcoming** votes (not past ones)

---

## 🔧 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| OpenWebUI | http://localhost:3000 | Chat interface |
| Backend API | http://localhost:8000 | REST API |
| API Docs | http://localhost:8000/docs | Interactive docs |
| Health | http://localhost:8000/health | Status check |

---

## 🔄 Updating Data

When new initiatives are added to swissvotes.ch:

```bash
# 1. Pull latest data from GitHub (if scraper ran)
git pull

# 2. Re-run migration to update database
python scripts/migrate_data.py

# 3. Re-index brochures if texts changed
python scripts/index_brochures.py
```

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check if API key is set
cat .env | grep SWISS_AI_PLATFORM_API_KEY

# Check backend logs
docker-compose logs backend
```

### Database connection fails

```bash
# Verify DATABASE_URL is correct
cat .env | grep DATABASE_URL

# Test connection from backend container
docker-compose exec backend python -c "from database import test_connection; test_connection()"
```

### No initiatives returned

```bash
# Check if migration ran successfully
python scripts/migrate_data.py

# Check database
docker-compose exec backend python -c "from database import get_db_session; from models import Initiative; session = get_db_session().__enter__(); print(f'Initiatives: {len(session.query(Initiative).all())}')"
```

---

## 💡 Next Steps

1. Add your Swisscom API key to `.env`
2. Add your Railway PostgreSQL URL to `.env`
3. Run migrations
4. Test the API endpoints
5. Open OpenWebUI and start asking questions!

---

**Questions?** Check:
- [README.md](README.md) - Project overview
- [STEP2-COMPLETE.md](STEP2-COMPLETE.md) - Database & RAG details
- [SETUP.md](SETUP.md) - Detailed setup guide
