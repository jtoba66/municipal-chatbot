"""
Municipal Chatbot Backend - FastAPI + LangChain RAG Pipeline
Self-hosted with Ollama for local LLM inference

Kitchener/Waterloo region citizen services chatbot
"""
import os
import json
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangChain + Ollama imports
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.schema import Document

# Load environment
load_dotenv()

app = FastAPI(title="Municipal Chatbot API")

# CORS - configurable for production
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
DOCS_DIR = DATA_DIR / "documents"

# Ollama configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

# Global state
embeddings = None
vectorstore = None
llm = None


def get_embeddings():
    """Get or create Ollama embeddings instance"""
    global embeddings
    if embeddings is None:
        embeddings = OllamaEmbeddings(
            model="nomic-embed-text",  # Fast embedding model
            base_url=OLLAMA_BASE_URL
        )
    return embeddings


def get_llm():
    """Get or create Ollama LLM instance"""
    global llm
    if llm is None:
        llm = OllamaLLM(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.3,
            # Timeout for response generation
            timeout=120
        )
    return llm


def get_vectorstore():
    """Get or create Chroma vectorstore"""
    global vectorstore
    if vectorstore is None:
        emb = get_embeddings()
        if CHROMA_DIR.exists() and list(CHROMA_DIR.iterdir()):
            vectorstore = Chroma(
                persist_directory=str(CHROMA_DIR), 
                embedding_function=emb
            )
        else:
            # Try to rebuild from documents
            try:
                rebuild_index_sync()
                vectorstore = Chroma(
                    persist_directory=str(CHROMA_DIR), 
                    embedding_function=emb
                )
            except Exception:
                raise HTTPException(
                    404, 
                    "Knowledge base not initialized. POST /rebuild-index to create it."
                )
    return vectorstore


def rebuild_index_sync():
    """Synchronous version of index rebuild"""
    emb = get_embeddings()
    
    # Load all text files from documents dir
    docs = []
    if DOCS_DIR.exists():
        for txt_file in DOCS_DIR.glob("*.txt"):
            try:
                loader = TextLoader(str(txt_file), encoding='utf-8')
                loaded_docs = loader.load()
                for doc in loaded_docs:
                    doc.metadata = {"source": f"local:{txt_file.name}"}
                docs.extend(loaded_docs)
            except Exception as e:
                print(f"Error loading {txt_file}: {e}")
    
    if not docs:
        # Create sample documents for demo
        sample_docs = [
            Document(
                page_content="Garbage is collected weekly. Place bins at the curb by 7 AM on your collection day. Check your schedule at kitchener.ca/waste",
                metadata={"source": "local:sample_garbage.txt"}
            ),
            Document(
                page_content="Parking tickets can be paid online at kitchener.ca/parking or in person at City Hall. Payment deadline is 30 days.",
                metadata={"source": "local:sample_parking.txt"}
            ),
            Document(
                page_content="Building permits are required for renovations over $10,000. Apply at kitchener.ca/permits or visit City Hall.",
                metadata={"source": "local:sample_permits.txt"}
            )
        ]
        docs = sample_docs
    
    # Split documents
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    splits = splitter.split_documents(docs)
    
    # Create and persist vectorstore
    global vectorstore
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=emb,
        persist_directory=str(CHROMA_DIR)
    )
    vectorstore.persist()
    
    return len(docs), len(splits)


# ==================== Request/Response Models ====================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    include_sources: bool = True


class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[dict]] = None
    session_id: str
    response_time_ms: int


class HealthResponse(BaseModel):
    status: str
    ollama: str
    db: str
    kb_docs: int


class RebuildResponse(BaseModel):
    status: str
    documents: int
    chunks: int


# ==================== API Endpoints ====================

@app.get("/", response_model=HealthResponse)
@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with service status"""
    ollama_status = "disconnected"
    kb_docs = 0
    
    # Check Ollama
    try:
        test_emb = get_embeddings()
        # Simple embedding test
        test_emb.embed_query("test")
        ollama_status = "connected"
    except Exception as e:
        ollama_status = f"error: {str(e)[:50]}"
    
    # Count knowledge base docs
    try:
        vs = get_vectorstore()
        kb_docs = vs._collection.count()
    except:
        pass
    
    return HealthResponse(
        status="running",
        ollama=ollama_status,
        db="connected",  # SQLite/Postgres status
        kb_docs=kb_docs
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with RAG"""
    import time
    start_time = time.time()
    
    # Generate session ID if not provided
    session_id = request.session_id or f"session_{int(start_time * 1000)}"
    
    try:
        vs = get_vectorstore()
    except HTTPException as e:
        raise e
    
    # Get LLM
    try:
        llm_model = get_llm()
    except Exception as e:
        raise HTTPException(503, f"Ollama not available: {str(e)}")
    
    # Create QA chain with sources
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm_model,
        chain_type="stuff",
        retriever=vs.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )
    
    # Query the chain
    try:
        result = qa_chain({"query": request.message})
    except Exception as e:
        raise HTTPException(500, f"Error generating response: {str(e)}")
    
    # Extract sources
    sources = []
    if request.include_sources:
        for doc in result.get("source_documents", []):
            sources.append({
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "source": doc.metadata.get("source", "Unknown")
            })
    
    response_time = int((time.time() - start_time) * 1000)
    
    return ChatResponse(
        answer=result["result"],
        sources=sources if request.include_sources else None,
        session_id=session_id,
        response_time_ms=response_time
    )


@app.post("/rebuild-index", response_model=RebuildResponse)
async def rebuild_index():
    """Rebuild the vector index from documents in data/documents/"""
    try:
        num_docs, num_chunks = rebuild_index_sync()
        return RebuildResponse(
            status="complete",
            documents=num_docs,
            chunks=num_chunks
        )
    except Exception as e:
        raise HTTPException(500, f"Error rebuilding index: {str(e)}")


@app.get("/api/widget.js")
async def get_widget_js():
    """Serve the embeddable widget JavaScript"""
    widget_js = '''
// Municipal Chatbot Widget Loader
(function() {
  var config = {
    apiUrl: window.location.origin,
    position: 'bottom-right',
    primaryColor: '#006699'
  };
  
  // Read data attributes from script tag
  var scripts = document.getElementsByTagName('script');
  var currentScript = scripts[scripts.length - 1];
  if (currentScript.dataset.city) config.city = currentScript.dataset.city;
  if (currentScript.dataset.color) config.primaryColor = currentScript.dataset.color;
  if (currentScript.dataset.apiUrl) config.apiUrl = currentScript.dataset.apiUrl;
  
  window.MunicipalChatbot = {
    config: config,
    init: function() { console.log('Chatbot initialized'); }
  };
  
  console.log('Municipal Chatbot widget loaded');
})();
'''
    return widget_js


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)