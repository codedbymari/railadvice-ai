import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Import your modules
from .document_manager import EnhancedFileDocumentManager
from .ai_engine import RailAdviceAI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
doc_manager = None
ai_engine = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global doc_manager, ai_engine
    logger.info("🚀 Initializing RailAdvice AI System...")
    
    try:
        # Initialize document manager
        doc_manager = EnhancedFileDocumentManager()
        logger.info("✅ Document manager loaded")

        # Load external documents if they exist
        if hasattr(doc_manager, 'load_external_documents'):
            doc_manager.load_external_documents()
            logger.info("✅ External documents loaded")
        
        # Initialize AI engine
        ai_engine = RailAdviceAI()
        logger.info("✅ AI engine loaded with knowledge base")
        
        # Get initial stats
        doc_count = len(doc_manager.list_documents())
        logger.info(f"📊 Knowledge base initialized with {doc_count} documents")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {e}")
        doc_manager = None
        ai_engine = None
    
    yield
    logger.info("🔄 Shutting down RailAdvice AI System...")

app = FastAPI(
    title="RailAdvice AI Backend",
    description="AI-powered railway consulting assistant - Backend API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS setup - Allow frontend domains
FRONTEND_URLS = [
    "https://railadvice-frontend.vercel.app",  # Replace with your Vercel domain
    "https://your-custom-domain.com",         # Replace with custom domain
    "http://localhost:3000",                  # Local development
    "http://localhost:8080",                  # Local development
    "http://127.0.0.1:3000",                  # Local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_URLS + ["*"],  # Remove "*" in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class ChatMessage(BaseModel):
    message: str
    context: str = "general"

class ChatResponse(BaseModel):
    response: str
    sources: int
    confidence: str
    intent_categories: list = []
    specific_terms: list = []
    analysis_summary: str = ""

# Health check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        doc_manager_ok = doc_manager is not None
        ai_engine_ok = ai_engine is not None
        
        doc_count = 0
        if doc_manager_ok:
            try:
                doc_count = len(doc_manager.list_documents())
            except:
                doc_manager_ok = False
        
        status = "healthy" if (doc_manager_ok and ai_engine_ok) else "partial"
        
        return {
            "status": status,
            "doc_manager_loaded": doc_manager_ok,
            "ai_engine_loaded": ai_engine_ok,
            "documents_count": doc_count,
            "service": "RailAdvice AI Backend",
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "error", "error": str(e)}

# Chat endpoint
@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Chat with RailAdvice AI"""
    if not ai_engine:
        raise HTTPException(status_code=503, detail="AI engine not available")
    
    if not message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        logger.info(f"Processing query: {message.message}")
        
        result = ai_engine.query(message.message)
        
        analysis_summary = f"Processed with {result['confidence']} confidence"
        if result['sources'] > 0:
            analysis_summary += f" using {result['sources']} sources"
        
        return ChatResponse(
            response=result["answer"],
            sources=result["sources"],
            confidence=result["confidence"],
            intent_categories=result.get("intent_categories", []),
            specific_terms=result.get("specific_terms", []),
            analysis_summary=analysis_summary
        )
    
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail="Error processing your question")

# Greeting endpoint
@app.get("/api/greet")
async def greet():
    """Get AI greeting message"""
    try:
        doc_count = len(doc_manager.list_documents()) if doc_manager else 0
        greeting = f"Hei! Jeg er RailAdvice AI-assistenten din med tilgang til {doc_count} dokumenter. Jeg kan hjelpe deg med ETCS, jernbaneteknologi og RailAdvice sine prosjekter."
        return {"greeting": greeting}
    except Exception as e:
        logger.error(f"Error getting greeting: {e}")
        return {"greeting": "Hei! Jeg er RailAdvice AI-assistenten din."}

# Stats endpoint
@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    if not doc_manager:
        raise HTTPException(status_code=503, detail="Document manager not available")

    try:
        stats = doc_manager.get_stats()
        
        if ai_engine:
            stats["ai_engine"] = {
                "loaded": True,
                "documents_in_ai": len(ai_engine.documents_text) if hasattr(ai_engine, 'documents_text') else 0
            }
        else:
            stats["ai_engine"] = {"loaded": False}
            
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

# Root endpoint
@app.get("/")
async def root():
    """API information"""
    try:
        doc_count = len(doc_manager.list_documents()) if doc_manager else 0
        ai_loaded = ai_engine is not None
        
        return {
            "message": "RailAdvice AI Backend API", 
            "version": "1.0.0",
            "status": "running",
            "ai_loaded": ai_loaded,
            "documents": doc_count,
            "endpoints": {
                "health": "/api/health",
                "chat": "/api/chat",
                "greet": "/api/greet",
                "stats": "/api/stats",
                "docs": "/docs"
            }
        }
    except Exception as e:
        logger.error(f"Error in root endpoint: {e}")
        return {"message": "RailAdvice AI Backend API", "error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)