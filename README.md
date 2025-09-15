# RailAdvice AI 🚆

An AI-powered railway consulting assistant. RailAdvice AI combines domain expertise in railway projects and regulations with  AI technology to provide intelligent support for RailAdvice consultants.

## Project Overview

- **Centralizing regulations and documentation** in one accessible location
- **Automating repetitive tasks** like reporting, data analysis, and status updates
- **Providing prioritization and decision support** based on project data and resource usage
- **Improving consistency and efficiency** across projects through reusable digital tools

**Demo**: https://railadvice-frontend.vercel.app

##  Tech Stack

### Backend
- **Python 3.8+** - Core runtime
- **FastAPI** - Modern async web framework
- **ChromaDB** - Vector database for document storage
- **SentenceTransformers** - AI embeddings for semantic search
- **spaCy** - Natural language processing

### AI/ML Components
- **OpenAI embeddings** - Document vectorization
- **TF-IDF** - Text analysis and keyword extraction
- **Custom neural search** - Semantic document retrieval
- **Contextual AI** - Conversation memory and context awareness

### Infrastructure
- **Railway** - Backend deployment
- **Docker** - Containerization support



## Project Structure

```
railadvice-ai/
├── main.py                 
├── src/                    
│   ├── document_manager.py # Document storage and indexing
│   ├── ai_engine.py       # AI query processing and responses
│   └── __init__.py
├── documents/             
│   ├── content/          
│   └── document_index.json # 
├── data/                 
│   └── chromadb/        
├── api/                  
│   ├── index.py       
├── projects/             # Railway project documents (JSON)
├── regulations/          # Railway regulations and standards
├── requirements.txt      
├── Dockerfile          
├── Procfile            
└── startup.sh          
```

##   Features

### Intelligent Query Processing
- **Natural Language Understanding**: Processes questions in Norwegian and English
- **Context Awareness**: Maintains conversation history and context
- **Intent Classification**: Identifies greeting, technical questions, help requests
- **Semantic Search**: Finds relevant documents using vector similarity

### Document Analysis
- **Full-text Search**: Fast document content searching
- **Metadata Extraction**: Automatic categorization and tagging
- **Risk Assessment**: Identifies missing requirements and compliance issues
- **Multi-format Support**: JSON, text, and structured document formats

### Railway Domain Expertise
- **ETCS/ERTMS Knowledge**: European train control systems
- **RAMS Analysis**: Reliability, Availability, Maintainability, Safety
- **TSI Compliance**: Technical Specifications for Interoperability
- **Project Management**: Cost estimation, timeline planning, resource allocation

##  AI Architecture

### Document Storage
- **ChromaDB**: Vector database for semantic search
- **File-based indexing**: JSON metadata storage
- **Lazy loading**: AI components initialize on demand

### Neural Pipeline
1. **Document Ingestion**: Text preprocessing and chunking
2. **Embedding Generation**: SentenceTransformer vectorization
3. **Index Creation**: ChromaDB vector storage
4. **Query Processing**: Semantic similarity matching
5. **Response Generation**: Context-aware answer synthesis

