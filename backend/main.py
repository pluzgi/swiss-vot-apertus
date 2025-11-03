"""
Swiss Voting Assistant - FastAPI Backend
Provides API endpoints and OpenWebUI Pipeline integration
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import logging
from datetime import datetime

from config import settings

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
# Initiative API Endpoints (Placeholder)
# ========================================

@app.get("/api/initiatives")
async def get_initiatives():
    """
    Get all upcoming Swiss initiatives
    TODO: Implement in Step 2 with database integration
    """
    logger.info("GET /api/initiatives called")
    return {
        "message": "Initiative listing endpoint - To be implemented in Step 2",
        "federal_initiatives": []
    }


@app.get("/api/initiatives/{vote_id}")
async def get_initiative(vote_id: str):
    """
    Get specific initiative by ID
    TODO: Implement in Step 2 with database integration
    """
    logger.info(f"GET /api/initiatives/{vote_id} called")
    return {
        "message": f"Initiative detail endpoint for {vote_id} - To be implemented in Step 2",
        "vote_id": vote_id
    }


@app.post("/api/search")
async def search_initiatives(query: InitiativeQuery):
    """
    Search initiatives by keyword
    TODO: Implement in Step 2 with database integration
    """
    logger.info(f"POST /api/search called with query: {query.query}")
    return {
        "message": "Search endpoint - To be implemented in Step 2",
        "query": query.query,
        "results": []
    }


@app.post("/api/rag/query")
async def rag_query(query: InitiativeQuery):
    """
    RAG-enabled semantic search
    TODO: Implement in Step 2 with ChromaDB integration
    """
    logger.info(f"POST /api/rag/query called with query: {query.query}")
    return {
        "message": "RAG query endpoint - To be implemented in Step 2",
        "query": query.query,
        "context": [],
        "answer": "RAG pipeline not yet implemented"
    }


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
