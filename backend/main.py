"""
Swiss Voting Assistant - FastAPI Backend
Provides API endpoints and OpenWebUI Pipeline integration
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
from datetime import datetime

from config import settings
from database import get_db, get_all_initiatives, get_initiative_by_vote_id, search_initiatives_by_keyword
from rag import get_rag_pipeline
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Swiss Voting Assistant API",
    description="Backend API for Swiss voting information with RAG capabilities",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# Pydantic Models
# ========================================

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    environment: str


class InitiativeQuery(BaseModel):
    query: str
    language: Optional[str] = "de"
    top_k: Optional[int] = 5


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    stream: Optional[bool] = False


# ========================================
# Health Check Endpoint
# ========================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow().isoformat(),
        version="1.0.0",
        environment=settings.ENVIRONMENT
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Swiss Voting Assistant API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }


# ========================================
# Initiative API Endpoints
# ========================================

@app.get("/api/initiatives")
async def get_initiatives(limit: int = 100, db: Session = Depends(get_db)):
    """Get all upcoming Swiss popular initiatives"""
    logger.info(f"GET /api/initiatives called (limit={limit})")

    try:
        initiatives = get_all_initiatives(db, limit=limit)
        return {
            "count": len(initiatives),
            "initiatives": [init.to_dict() for init in initiatives]
        }
    except Exception as e:
        logger.error(f"Error fetching initiatives: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch initiatives")


@app.get("/api/initiatives/{vote_id}")
async def get_initiative(vote_id: str, db: Session = Depends(get_db)):
    """Get specific initiative by vote ID"""
    logger.info(f"GET /api/initiatives/{vote_id} called")

    try:
        initiative = get_initiative_by_vote_id(db, vote_id)

        if not initiative:
            raise HTTPException(status_code=404, detail=f"Initiative {vote_id} not found")

        return initiative.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching initiative {vote_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch initiative")


@app.post("/api/search")
async def search_initiatives(query: InitiativeQuery, db: Session = Depends(get_db)):
    """Search initiatives by keyword in title or policy area"""
    logger.info(f"POST /api/search called with query: {query.query}")

    try:
        results = search_initiatives_by_keyword(
            db,
            keyword=query.query,
            limit=query.top_k or 10
        )

        return {
            "query": query.query,
            "count": len(results),
            "results": [init.to_dict() for init in results]
        }

    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")


@app.post("/api/rag/query")
async def rag_query(query: InitiativeQuery):
    """RAG-enabled semantic search through brochure texts"""
    logger.info(f"POST /api/rag/query called with query: {query.query}")

    try:
        rag_pipeline = get_rag_pipeline()

        result = rag_pipeline.query_with_context(
            query=query.query,
            language=query.language or "de",
            top_k=query.top_k or 5,
            include_metadata=True
        )

        return result

    except Exception as e:
        logger.error(f"RAG query error: {e}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


# ========================================
# OpenWebUI Pipeline Endpoints
# ========================================

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    """
    OpenAI-compatible chat completions endpoint
    This will be used by OpenWebUI as the LLM backend
    TODO: Implement in Step 3 with Swisscom Apertus integration
    """
    logger.info(f"POST /v1/chat/completions called with {len(request.messages)} messages")

    # Placeholder response
    return {
        "id": "chatcmpl-placeholder",
        "object": "chat.completion",
        "created": int(datetime.utcnow().timestamp()),
        "model": "apertus-70b",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Swiss Voting Assistant pipeline is being configured. Swisscom Apertus integration coming in Step 3."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }
    }


@app.get("/v1/models")
async def list_models():
    """
    List available models (OpenAI-compatible endpoint)
    """
    return {
        "object": "list",
        "data": [
            {
                "id": "apertus-70b",
                "object": "model",
                "created": int(datetime.utcnow().timestamp()),
                "owned_by": "swisscom"
            }
        ]
    }


# ========================================
# Error Handlers
# ========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ========================================
# Startup/Shutdown Events
# ========================================

@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("Swiss Voting Assistant API Starting")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"ChromaDB Host: {settings.CHROMADB_HOST}:{settings.CHROMADB_PORT}")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Swiss Voting Assistant API Shutting Down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.LOG_LEVEL.lower()
    )
