import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import logging

# Import both document manager and AI engine
from src.document_manager import EnhancedFileDocumentManager
from src.ai_engine import RailAdviceAI

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
        
        # Initialize AI engine with manual documents
        ai_engine = RailAdviceAI(use_manual_docs=True)
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
    title="RailAdvice AI API",
    description="AI-powered railway consulting assistant",
    version="3.2.0",
    lifespan=lifespan
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# Data models
# ---------------------------
class DocumentRequest(BaseModel):
    title: str
    content: str
    doc_type: str = "general"
    category: str = "general"
    tags: list[str] = []
    metadata: dict = {}

class DocumentUpdateRequest(BaseModel):
    title: str | None = None
    content: str | None = None
    doc_type: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    metadata: dict | None = None

class SearchRequest(BaseModel):
    query: str | None = None
    doc_type: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    limit: int = 50

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

# ---------------------------
# Utility functions
# ---------------------------
def safe_reload_ai():
    """Safely reload AI engine with error handling"""
    global ai_engine
    if ai_engine:
        try:
            ai_engine.reload_documents()
            logger.info("🔄 AI engine reloaded with updated documents")
            return True
        except Exception as e:
            logger.error(f"⚠️ Failed to reload AI engine: {e}")
            return False
    return False

def check_services():
    """Check if required services are available"""
    if not doc_manager:
        raise HTTPException(status_code=503, detail="Document manager not available")
    if not ai_engine:
        raise HTTPException(status_code=503, detail="AI engine not available")

# ---------------------------
# Document Management API endpoints
# ---------------------------

@app.post("/api/documents")
async def add_document(req: DocumentRequest):
    if not doc_manager:
        raise HTTPException(status_code=503, detail="Document manager not available")

    try:
        doc_id = doc_manager.add_document(
            title=req.title,
            content=req.content,
            doc_type=req.doc_type,
            category=req.category,
            tags=req.tags,
            metadata=req.metadata
        )
        
        # Reload AI engine to include new document
        reload_success = safe_reload_ai()
        
        return {
            "id": doc_id, 
            "status": "created",
            "ai_reloaded": reload_success
        }
    except Exception as e:
        logger.error(f"Error adding document: {e}")
        raise HTTPException(status_code=500, detail="Failed to add document")


@app.get("/api/documents/{doc_id}")
async def get_document(doc_id: str):
    if not doc_manager:
        raise HTTPException(status_code=503, detail="Document manager not available")

    try:
        doc = doc_manager.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve document")


@app.get("/api/documents")
async def list_documents(limit: int = 100):
    if not doc_manager:
        raise HTTPException(status_code=503, detail="Document manager not available")

    try:
        documents = doc_manager.list_documents(limit=limit)
        return {"documents": documents, "count": len(documents)}
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to list documents")


@app.post("/api/search")
async def search_documents(req: SearchRequest):
    if not doc_manager:
        raise HTTPException(status_code=503, detail="Document manager not available")

    try:
        results = doc_manager.search_documents(
            query=req.query,
            doc_type=req.doc_type,
            category=req.category,
            tags=req.tags,
            limit=req.limit
        )
        return {"results": results, "count": len(results)}
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to search documents")


@app.delete("/api/documents/{doc_id}")
async def delete_document(doc_id: str):
    if not doc_manager:
        raise HTTPException(status_code=503, detail="Document manager not available")

    try:
        success = doc_manager.remove_document(doc_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Reload AI engine after deletion
        reload_success = safe_reload_ai()
        
        return {
            "status": "deleted", 
            "id": doc_id,
            "ai_reloaded": reload_success
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document")


@app.put("/api/documents/{doc_id}")
async def update_document(doc_id: str, req: DocumentUpdateRequest):
    if not doc_manager:
        raise HTTPException(status_code=503, detail="Document manager not available")

    try:
        # Filter out None values
        update_data = {k: v for k, v in req.model_dump().items() if v is not None}
        
        updated = doc_manager.update_document(doc_id, **update_data)
        if not updated:
            raise HTTPException(status_code=404, detail="Document not found or update failed")
        
        # Reload AI engine after update
        reload_success = safe_reload_ai()
        
        return {
            "status": "updated", 
            "id": doc_id,
            "ai_reloaded": reload_success
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update document")


@app.get("/api/stats")
async def get_stats():
    if not doc_manager:
        raise HTTPException(status_code=503, detail="Document manager not available")

    try:
        stats = doc_manager.get_stats()
        
        # Add AI engine stats if available
        if ai_engine:
            stats["ai_engine"] = {
                "loaded": True,
                "documents_in_ai": len(ai_engine.documents_text) if hasattr(ai_engine, 'documents_text') else 0,
                "embedder_model": "all-MiniLM-L6-v2"
            }
        else:
            stats["ai_engine"] = {"loaded": False}
            
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

# ---------------------------
# AI Chat endpoints
# ---------------------------

@app.get("/api/greet")
async def greet():
    """Get AI greeting message"""
    if not ai_engine:
        raise HTTPException(status_code=503, detail="AI engine not available")
    
    try:
        greeting = ai_engine.get_greeting()
        return {"greeting": greeting}
    except Exception as e:
        logger.error(f"Error getting greeting: {e}")
        return {"greeting": "RailAdvice AI er ikke tilgjengelig for øyeblikket."}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Chat with RailAdvice AI"""
    if not ai_engine:
        raise HTTPException(status_code=503, detail="AI engine not available")
    
    if not message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    try:
        logger.info(f"Processing query: {message.message}")
        
        # Query the AI engine directly
        result = ai_engine.query(message.message)
        
        # Create analysis summary
        analysis_summary = f"Processed with {result['confidence']} confidence"
        if result['sources'] > 0:
            analysis_summary += f" using {result['sources']} sources"
        if result['intent_categories']:
            analysis_summary += f". Intent: {', '.join(result['intent_categories'])}"
        
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


@app.get("/api/ai-status")
async def ai_status():
    """Get AI system status"""
    try:
        doc_count = len(doc_manager.list_documents()) if doc_manager else 0
        ai_doc_count = len(ai_engine.documents_text) if (ai_engine and hasattr(ai_engine, 'documents_text')) else 0
        
        return {
            "ai_engine_loaded": ai_engine is not None,
            "doc_manager_loaded": doc_manager is not None,
            "documents_count": doc_count,
            "ai_documents_loaded": ai_doc_count,
            "ai_knowledge_status": "loaded" if ai_engine else "not_loaded",
            "system_health": "healthy" if (doc_manager and ai_engine and doc_count > 0) else "needs_attention"
        }
    except Exception as e:
        logger.error(f"Error getting AI status: {e}")
        return {
            "ai_engine_loaded": False,
            "doc_manager_loaded": False,
            "error": str(e)
        }


@app.post("/api/reload-ai")
async def reload_ai():
    """Force reload AI engine (useful after adding documents)"""
    if not ai_engine:
        raise HTTPException(status_code=503, detail="AI engine not available")
    
    try:
        logger.info("Manual AI reload requested")
        success = safe_reload_ai()
        
        if success:
            doc_count = len(ai_engine.documents_text) if hasattr(ai_engine, 'documents_text') else 0
            return {
                "status": "success", 
                "message": f"AI engine reloaded successfully with {doc_count} documents"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reload AI engine")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reloading AI: {e}")
        raise HTTPException(status_code=500, detail="Failed to reload AI engine")


# ---------------------------
# Health and system endpoints
# ---------------------------

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Comprehensive health check"""
    try:
        doc_manager_ok = doc_manager is not None
        ai_engine_ok = ai_engine is not None
        
        doc_count = 0
        ai_doc_count = 0
        
        if doc_manager_ok:
            try:
                doc_count = len(doc_manager.list_documents())
            except:
                doc_manager_ok = False
                
        if ai_engine_ok:
            try:
                ai_doc_count = len(ai_engine.documents_text) if hasattr(ai_engine, 'documents_text') else 0
            except:
                ai_engine_ok = False
        
        status = "healthy" if (doc_manager_ok and ai_engine_ok and doc_count > 0) else "partial"
        
        return {
            "status": status,
            "doc_manager_loaded": doc_manager_ok,
            "ai_engine_loaded": ai_engine_ok,
            "documents_count": doc_count,
            "ai_documents_loaded": ai_doc_count,
            "service": "RailAdvice AI",
            "version": "3.2.0"
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "service": "RailAdvice AI"
        }

# ---------------------------
# Static file serving
# ---------------------------

# Serve static frontend if exists
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve images if exists
if os.path.exists("img"):
    app.mount("/img", StaticFiles(directory="img"), name="images")

@app.get("/")
async def serve_frontend():
    """Serve frontend or API info"""
    html_path = Path("static") / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    else:
        try:
            # Get system status for API root
            doc_count = len(doc_manager.list_documents()) if doc_manager else 0
            ai_loaded = ai_engine is not None
            
            return {
                "message": "RailAdvice AI API running", 
                "version": "3.2.0",
                "docs": "/docs",
                "health": "/api/health",
                "ai_status": f"AI Engine: {'✅' if ai_loaded else '❌'}, Documents: {doc_count}",
                "endpoints": {
                    "chat": "/api/chat",
                    "documents": "/api/documents",
                    "stats": "/api/stats"
                }
            }
        except Exception as e:
            logger.error(f"Error in root endpoint: {e}")
            return {
                "message": "RailAdvice AI API running with errors", 
                "docs": "/docs",
                "error": str(e)
            }


if __name__ == "__main__":
    print("🚆 Starting RailAdvice AI API Server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )