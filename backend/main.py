"""
Municipal Chatbot Backend - FastAPI + LangChain RAG Pipeline
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
from langchain.document_loaders import BSHTMLLoader, WebBaseLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_openai import OpenAI

# Load environment
load_dotenv()

app = FastAPI(title="Municipal Chatbot API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
DOCS_DIR = DATA_DIR / "documents"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
CHROMA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)

# Initialize embeddings and vectorstore globally
embeddings = None
vectorstore = None


def get_embeddings():
    global embeddings
    if embeddings is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(500, "OPENAI_API_KEY not configured")
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small", api_key=api_key)
    return embeddings


def get_vectorstore():
    global vectorstore
    if vectorstore is None:
        emb = get_embeddings()
        if CHROMA_DIR.exists() and list(CHROMA_DIR.iterdir()):
            vectorstore = Chroma(persist_directory=str(CHROMA_DIR), embedding_function=emb)
        else:
            raise HTTPException(404, "Knowledge base not initialized. Run data ingestion first.")
    return vectorstore


class ChatRequest(BaseModel):
    message: str
    include_sources: bool = True


class ChatResponse(BaseModel):
    answer: str
    sources: Optional[List[dict]] = None


class HealthResponse(BaseModel):
    status: str
    kb_loaded: bool


@app.get("/", response_model=HealthResponse)
async def health_check():
    kb_loaded = False
    try:
        vs = get_vectorstore()
        kb_loaded = vs is not None
    except:
        pass
    return HealthResponse(status="running", kb_loaded=kb_loaded)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with RAG"""
    try:
        vs = get_vectorstore()
    except HTTPException as e:
        raise e

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(500, "OPENAI_API_KEY not configured")

    llm = OpenAI(model="gpt-4o-mini", api_key=api_key, temperature=0.3)

    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vs.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

    # Query
    result = qa_chain({"query": request.message})

    # Extract sources
    sources = []
    if request.include_sources:
        for doc in result.get("source_documents", []):
            sources.append({
                "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                "source": doc.metadata.get("source", "Unknown")
            })

    return ChatResponse(
        answer=result["result"],
        sources=sources if request.include_sources else None
    )


@app.post("/rebuild-index")
async def rebuild_index():
    """Rebuild the vector index from documents"""
    global vectorstore
    
    emb = get_embeddings()
    
    # Load all text files from documents dir
    docs = []
    for txt_file in DOCS_DIR.glob("*.txt"):
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            from langchain.schema import Document
            doc = Document(
                page_content=content,
                metadata={"source": f"local:{txt_file.name}"}
            )
            docs.append(doc)
    
    if not docs:
        raise HTTPException(404, "No documents found in data/documents/")
    
    # Split
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_documents(docs)
    
    # Create vectorstore
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=emb,
        persist_directory=str(CHROMA_DIR)
    )
    vectorstore.persist()
    
    return {"status": "index rebuilt", "documents": len(docs), "chunks": len(splits)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)