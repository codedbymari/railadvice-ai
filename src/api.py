import sys
import os
import asyncio
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Setup logging with better configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Global instances with better state management
class AppState:
    def __init__(self):
        self.doc_manager: Optional[object] = None
        self.ai_engine: Optional[object] = None
        self.ai_loading = False
        self.ai_loaded = False
        self.initialization_lock = asyncio.Lock()

app_state = AppState()

# Lazy imports to speed up startup
def get_modules():
    """Lazy import modules only when needed"""
    try:
        from src.document_manager import EnhancedFileDocumentManager
        from src.ai_engine import RailAdviceAI, create_ai_engine
        return EnhancedFileDocumentManager, RailAdviceAI, create_ai_engine
    except ImportError as e:
        logger.error(f"Failed to import modules: {e}")
        raise

async def initialize_document_manager():
    """Initialize document manager with better error handling"""
    if app_state.doc_manager is not None:
        return True
        
    try:
        EnhancedFileDocumentManager, _, _ = get_modules()
        app_state.doc_manager = EnhancedFileDocumentManager()
        app_state.doc_manager.load_external_documents()
        logger.info("✅ Document manager initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Document manager initialization failed: {e}")
        return False

async def initialize_ai_engine():
    """Initialize AI engine with proper async handling"""
    async with app_state.initialization_lock:
        if app_state.ai_loaded or app_state.ai_loading:
            return app_state.ai_engine
            
        app_state.ai_loading = True
        
        try:
            logger.info("🧠 Initializing AI engine...")
            _, _, create_ai_engine = get_modules()
            
            # Run CPU-intensive initialization in thread pool
            loop = asyncio.get_event_loop()
            app_state.ai_engine = await loop.run_in_executor(
                None, lambda: create_ai_engine(lazy=False, contextual=True)
            )
            
            app_state.ai_loaded = True
            doc_count = getattr(app_state.ai_engine, 'documents_count', 0)
            logger.info(f"✅ AI engine initialized with {doc_count} documents")
            
        except Exception as e:
            logger.error(f"❌ AI engine initialization failed: {e}")
            app_state.ai_engine = None
            
        finally:
            app_state.ai_loading = False
            
        return app_state.ai_engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Optimized lifespan with faster startup"""
    logger.info("🚀 Starting RailAdvice AI System...")
    
    startup_tasks = []
    
    # Initialize document manager first (lightweight)
    startup_tasks.append(initialize_document_manager())
    
    # Start AI initialization in background
    startup_tasks.append(asyncio.create_task(initialize_ai_engine()))
    
    # Wait for document manager, let AI load in background
    try:
        doc_success = await startup_tasks[0]
        if not doc_success:
            logger.warning("⚠️ Document manager failed to initialize")
        else:
            logger.info("✅ Core system ready - AI loading in background")
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
    
    yield
    
    # Cleanup
    logger.info("Shutting down RailAdvice AI System...")

    # Cancel background tasks if still running
    for task in startup_tasks:
       if hasattr(task, 'done') and not task.done():
           task.cancel()
       elif hasattr(task, 'cancel'):
           task.cancel()

# Create FastAPI app with optimized settings
app = FastAPI(
    title="RailAdvice AI API",
    description="AI-powered railway consulting assistant",
    version="3.4.0",
    lifespan=lifespan,
    # Performance optimizations
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Optimized CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Specific methods instead of "*"
    allow_headers=["*"],
    max_age=600,  # Cache preflight requests
)

# ---------------------------
# Pydantic models with validation
# ---------------------------
class DocumentRequest(BaseModel):
    title: str
    content: str
    doc_type: str = "general"
    category: str = "general" 
    tags: list[str] = []
    metadata: dict = {}
    
    class Config:
        str_strip_whitespace = True  # Auto-strip whitespace
        max_anystr_length = 100000  # Prevent massive payloads

class ChatMessage(BaseModel):
    message: str
    context: str = "general"
    
    class Config:
        str_strip_whitespace = True
        max_anystr_length = 5000

class ChatResponse(BaseModel):
    response: str
    sources: int
    confidence: str
    ai_status: str = "ready"
    loading: bool = False

# ---------------------------
# Utility functions with caching
# ---------------------------
def get_ai_status() -> str:
    """Get current AI engine status"""
    if app_state.ai_loaded and app_state.ai_engine:
        return "ready"
    elif app_state.ai_loading:
        return "loading"
    elif app_state.ai_engine is None:
        return "not_loaded"
    else:
        return "error"

async def ensure_ai_ready(timeout: int = 30) -> bool:
    """Ensure AI engine is ready with timeout"""
    if app_state.ai_loaded:
        return True
        
    if not app_state.ai_loading:
        # Start initialization if not already running
        asyncio.create_task(initialize_ai_engine())
    
    # Wait for AI to be ready with timeout
    start_time = asyncio.get_event_loop().time()
    while app_state.ai_loading:
        if asyncio.get_event_loop().time() - start_time > timeout:
            return False
        await asyncio.sleep(0.5)
    
    return app_state.ai_loaded

# ---------------------------
# Health endpoints (cached responses)
# ---------------------------
@app.get("/health")
async def health():
    """Fast health check"""
    return {"status": "healthy", "service": "RailAdvice AI"}

@app.get("/api/health")
async def detailed_health():
    """Detailed health with status"""
    try:
        doc_manager_ready = app_state.doc_manager is not None
        ai_status = get_ai_status()
        doc_count = 0
        
        if doc_manager_ready:
            try:
                doc_count = len(app_state.doc_manager.list_documents())
            except:
                doc_count = 0
        
        return {
            "status": "healthy" if doc_manager_ready else "partial",
            "doc_manager": "ready" if doc_manager_ready else "error",
            "ai_engine": ai_status,
            "documents_count": doc_count,
            "version": "3.4.0",
            "uptime": True
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"status": "error", "error": str(e)}

@app.get("/")
async def root():
    """Root endpoint with system overview"""
    try:
        doc_count = 0
        if app_state.doc_manager:
            try:
                doc_count = len(app_state.doc_manager.list_documents())
            except:
                pass
                
        return {
            "message": "RailAdvice AI API", 
            "version": "3.4.0",
            "status": {
                "documents": doc_count,
                "ai_engine": get_ai_status(),
                "ready": app_state.doc_manager is not None
            },
            "endpoints": {
                "docs": "/docs",
                "health": "/api/health", 
                "chat": "/api/chat",
                "documents": "/api/documents",
                "ai_status": "/api/ai-status"
            }
        }
    except Exception as e:
        logger.error(f"Root endpoint error: {e}")
        return {
            "message": "RailAdvice AI API",
            "version": "3.4.0",
            "status": "error",
            "error": str(e)
        }

# ---------------------------
# AI endpoints with better error handling
# ---------------------------
@app.get("/api/ai-status")
async def ai_status_endpoint():
    """Get AI engine status"""
    return {
        "ai_engine_status": get_ai_status(),
        "ai_loading": app_state.ai_loading,
        "ai_loaded": app_state.ai_loaded,
        "doc_manager_ready": app_state.doc_manager is not None,
        "documents_count": len(app_state.doc_manager.list_documents()) if app_state.doc_manager else 0,
        "ready_for_chat": get_ai_status() == "ready"
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Enhanced chat endpoint with better async handling"""
    if not message.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    ai_status = get_ai_status()
    
    # Handle loading state
    if ai_status == "loading":
        return ChatResponse(
            response="AI engine is initializing. Please wait a moment and try again.",
            sources=0,
            confidence="system",
            ai_status="loading",
            loading=True
        )
    
    # Try to ensure AI is ready
    if ai_status != "ready":
        ai_ready = await ensure_ai_ready(timeout=10)
        if not ai_ready:
            return ChatResponse(
                response="AI engine is currently unavailable. Please try again later or contact support.",
                sources=0,
                confidence="system",
                ai_status="error"
            )
    
    try:
        logger.info(f"Processing query: {message.message[:100]}...")
        
        # Run AI query in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, 
            app_state.ai_engine.query, 
            message.message
        )
        
        return ChatResponse(
            response=result["answer"],
            sources=result.get("sources", 0),
            confidence=result.get("confidence", "medium"),
            ai_status="ready"
        )
        
    except Exception as e:
        logger.error(f"Chat processing error: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Sorry, I encountered an error processing your question. Please try again."
        )

# ---------------------------
# Document management with async
# ---------------------------
@app.get("/api/documents")
async def list_documents(limit: int = 100, offset: int = 0):
    """List documents with pagination"""
    if not app_state.doc_manager:
        raise HTTPException(status_code=503, detail="Document manager not available")
    
    try:
        # Run in thread pool for large document lists
        loop = asyncio.get_event_loop()
        documents = await loop.run_in_executor(
            None,
            lambda: app_state.doc_manager.list_documents(limit=limit)[offset:offset+limit]
        )
        
        return {
            "documents": documents,
            "count": len(documents),
            "offset": offset,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve documents")

@app.post("/api/documents")
async def add_document(req: DocumentRequest, background_tasks: BackgroundTasks):
    """Add document with background AI reload"""
    if not app_state.doc_manager:
        raise HTTPException(status_code=503, detail="Document manager not available")
    
    try:
        # Run document addition in thread pool
        loop = asyncio.get_event_loop()
        doc_id = await loop.run_in_executor(
            None,
            lambda: app_state.doc_manager.add_document(
                title=req.title,
                content=req.content,
                doc_type=req.doc_type,
                category=req.category,
                tags=req.tags,
                metadata=req.metadata
            )
        )
        
        # Reload AI in background if ready
        if app_state.ai_engine and app_state.ai_loaded:
            background_tasks.add_task(reload_ai_background)
        
        return {"id": doc_id, "status": "created", "title": req.title}
        
    except Exception as e:
        logger.error(f"Error adding document: {e}")
        raise HTTPException(status_code=500, detail="Failed to add document")

async def reload_ai_background():
    """Background task to reload AI documents"""
    if app_state.ai_engine and app_state.ai_loaded:
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                app_state.ai_engine.reload_documents
            )
            logger.info("🔄 AI engine reloaded with updated documents")
        except Exception as e:
            logger.error(f"Failed to reload AI engine: {e}")

@app.post("/api/initialize-ai")
async def force_initialize_ai():
    """Force AI initialization endpoint"""
    ai_status = get_ai_status()
    
    if ai_status == "ready":
        return {"status": "ready", "message": "AI engine is already loaded and ready"}
    
    if ai_status == "loading":
        return {"status": "loading", "message": "AI engine is currently initializing"}
    
    # Start initialization
    asyncio.create_task(initialize_ai_engine())
    return {"status": "started", "message": "AI engine initialization started in background"}

# ---------------------------
# Error handlers
# ---------------------------
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {"error": "Endpoint not found", "available_endpoints": ["/", "/docs", "/api/health", "/api/chat"]}

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {exc}")
    return {"error": "Internal server error", "message": "Please try again later"}

if __name__ == "__main__":
    print("🚆 Starting Optimized RailAdvice AI API Server...")
    
    # Production-ready uvicorn configuration
    config = {
        "host": "0.0.0.0",
        "port": int(os.getenv("PORT", 8000)),
        "log_level": "info",
        "access_log": False,  # Disable access logs for performance
        "workers": 1,  # Single worker for now, scale as needed
        "timeout_keep_alive": 5,
        "timeout_graceful_shutdown": 30
    }
    
    # Add performance optimizations only if available
    if sys.platform != "win32":
        try:
            import uvloop
            config["loop"] = "uvloop"
        except ImportError:
            logger.info("uvloop not available, using default asyncio")
    
    try:
        import httptools
        config["http"] = "httptools"
    except ImportError:
        logger.info("httptools not available, using default HTTP parser")
    
    try:
        uvicorn.run(app, **config)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)