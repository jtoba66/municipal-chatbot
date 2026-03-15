# Municipal Chatbot - System Architecture Specification

**Project:** Municipal Chatbot for Kitchener/Waterloo Region  
**Version:** 1.0  
**Architect:** Gilfoyle  
**Status:** Ready for Dinesh (Coder)

---

## 🏗️ High-Level Architecture

**Architecture Pattern**: Modular Monolith (FastAPI + React)  
**Communication Pattern**: REST API (HTTP/WebSocket for future)  
**Data Pattern**: Traditional CRUD + RAG for semantic search  
**Deployment Pattern**: Docker Compose (single-server deployment)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MUNICIPAL CHATBOT SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │   Citizens   │     │ City Staff   │     │  Researchers │                │
│  │  (Chat UI)   │     │  (Dashboard) │     │ (Data Mgmt)  │                │
│  └──────┬───────┘     └──────┬───────┘     └──────┬───────┘                │
│         │                    │                    │                         │
│         └────────────────────┼────────────────────┘                         │
│                              │                                              │
│                              ▼                                              │
│                    ┌─────────────────┐                                      │
│                    │   CDN / Nginx   │  (Static assets, SSL termination)  │
│                    └────────┬────────┘                                      │
│                             │                                               │
│         ┌───────────────────┼───────────────────┐                          │
│         ▼                   ▼                   ▼                          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │   Widget    │    │   Admin     │    │   Ingest    │                    │
│  │  (React)    │    │  Dashboard  │    │   Scripts   │                    │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘                    │
│         │                  │                  │                             │
│         └──────────────────┼──────────────────┘                             │
│                            ▼                                                │
│                  ┌───────────────────┐                                      │
│                  │  FastAPI Backend  │                                      │
│                  │     (Port 8000)   │                                      │
│                  └─────────┬─────────┘                                      │
│                            │                                                │
│         ┌──────────────────┼──────────────────┐                            │
│         ▼                  ▼                  ▼                            │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                    │
│  │  Ollama     │    │  PostgreSQL │    │   Chroma    │                    │
│  │  (LLM)      │    │  (Storage)  │    │ (Vector DB) │                    │
│  │  Port 11434 │    │  Port 5432  │    │  Local FS   │                    │
│  └─────────────┘    └─────────────┘    └─────────────┘                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🧩 Component Breakdown

### 1. Frontend (React + TypeScript)

| Component | Purpose | Location |
|-----------|---------|----------|
| **ChatWidget** | Embeddable chat interface | `frontend/widget/` |
| **AdminDashboard** | Analytics + content management | `frontend/dashboard/` |
| **SharedUI** | Buttons, inputs, modals | `frontend/components/` |

**Tech Stack:**
- React 18+ with TypeScript
- Tailwind CSS (styling)
- `react-chat-widget` or custom (chat UI)
- Vite (build tool)
- Zustand (lightweight state)

### 2. Backend (Python/FastAPI)

| Component | Purpose | Location |
|-----------|---------|----------|
| **API Server** | REST endpoints | `backend/api/` |
| **RAG Pipeline** | Content ingestion + retrieval | `backend/rag/` |
| **LLM Interface** | Ollama wrapper | `backend/llm/` |
| **Database** | SQLAlchemy models | `backend/db/` |

**Tech Stack:**
- FastAPI (web framework)
- LangChain + LangGraph (RAG orchestration)
- SQLAlchemy (ORM)
- Pydantic (validation)

### 3. Infrastructure

| Service | Purpose | Config |
|---------|---------|--------|
| **Ollama** | Local LLM inference | `ollama serve` on port 11434 |
| **PostgreSQL** | Relational data | Docker container |
| **Chroma** | Vector embeddings | Local filesystem |
| **Nginx** | Reverse proxy / SSL | Config file |
| **Docker Compose** | Orchestration | `docker-compose.yml` |

---

## 💾 Database Architecture

```sql
-- PostgreSQL Schema (MVP with SQLite option)

-- Knowledge base: Q&A content managed by admins
CREATE TABLE knowledge_base (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,          -- 'garbage', 'parking', 'permits', 'taxes', 'bylaws'
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources JSONB DEFAULT '[]'::jsonb,      -- [{url, title, accessed_at}]
    city VARCHAR(50) DEFAULT 'kitchener',   -- Multi-city support
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_kb_category ON knowledge_base(category);
CREATE INDEX idx_kb_city ON knowledge_base(city);

-- Conversations: Session tracking
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL UNIQUE,
    city VARCHAR(50) DEFAULT 'kitchener',
    user_agent TEXT,
    ip_hash VARCHAR(64),                    -- Hashed IP for analytics
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP
);

CREATE INDEX idx_conv_session ON conversations(session_id);
CREATE INDEX idx_conv_city ON conversations(city);

-- Messages: Individual messages
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL,              -- 'user' or 'assistant'
    content TEXT NOT NULL,
    sources JSONB,                          -- Citations for assistant messages
    response_time_ms INTEGER,
    token_count INTEGER,                    -- For cost tracking
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_msg_conv ON messages(conversation_id);

-- Feedback: User satisfaction
CREATE TABLE feedback (
    id SERIAL PRIMARY KEY,
    message_id INTEGER REFERENCES messages(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating BETWEEN 1 AND 5),
    feedback_text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Admin users (simple for MVP)
CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'editor',      -- 'admin' or 'editor'
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔌 API Design Specification

### Core Endpoints

#### Health & Status
```
GET /api/health
Response: { "status": "ok", "ollama": "connected", "db": "connected", "kb_docs": 142 }
```

#### Chat (Public)
```
POST /api/chat
Body: { 
  "message": "When is garbage day?", 
  "session_id": "abc-123",      // optional
  "include_sources": true       // optional, default true
}
Response: {
  "answer": "Garbage day for your address is...",
  "sources": [{"url": "https://kitchener.ca/...", "title": "Waste Collection Schedule"}],
  "session_id": "abc-123",
  "response_time_ms": 1450
}
```

#### Admin: Knowledge Base
```
GET /api/admin/knowledge?category=garbage&city=kitchener
Response: [{ "id": 1, "question": "...", "answer": "...", ... }]

POST /api/admin/knowledge
Body: { "category": "parking", "question": "...", "answer": "...", "sources": [...] }
Response: { "id": 42, "status": "created" }

PUT /api/admin/knowledge/{id}
Body: { "answer": "Updated answer..." }
Response: { "id": 42, "status": "updated" }

DELETE /api/admin/knowledge/{id}
Response: { "status": "deleted" }
```

#### Admin: Analytics
```
GET /api/admin/analytics?period=30d
Response: {
  "total_conversations": 1247,
  "total_messages": 3891,
  "avg_response_time_ms": 1820,
  "avg_rating": 4.3,
  "top_queries": [
    {"query": "garbage day", "count": 234},
    {"query": "parking ticket", "count": 189}
  ],
  "category_distribution": { "garbage": 342, "parking": 287, ... }
}
```

#### Admin: RAG Rebuild
```
POST /api/admin/rebuild-index
Response: { "status": "rebuilding", "documents": 150, "chunks": 892 }
GET /api/admin/rebuild-status
Response: { "status": "complete", "indexed_at": "2025-03-14T..." }
```

#### Embed Script
```
GET /api/widget.js
Response: JavaScript code for widget embed
```

---

## 🔄 Data Flow

```
User Question → Widget → API /chat → RAG Pipeline → Ollama → Response → Widget

Step-by-step:
1. User types: "When is my garbage collected?"
2. Widget sends POST /api/chat with message
3. Backend receives, looks up session (or creates new)
4. RAG Pipeline:
   a. Generate embedding for query via Ollama embeddings
   b. Search Chroma vector DB for similar chunks
   c. Retrieve top-k documents (k=3-5)
   d. Build prompt with retrieved context
5. Send prompt to Ollama (llama3.2 or phi3)
6. Ollama returns generated answer
7. Backend logs message to PostgreSQL
8. Return {answer, sources, session_id} to widget
9. Widget displays with source citations
10. Optional: User rates response (1-5 stars)
```

---

## 🛡️ Security Design

### Input Sanitization
- **LLM Input**: Strip HTML, scripts, SQL injection patterns before RAG
- **XSS Prevention**: React handles escaping; validate URLs in sources
- **Rate Limiting**: 60 requests/minute per IP (configurable)

### Content Filtering
- **Prompt Injection**: Prepend system prompt with guardrails
- **Harmful Content**: Ollama models are local; can be fine-tuned or filtered post-generation
- **Citation Verification**: Only allow sources from approved city domains

### Data Privacy
- **No PII Storage**: Conversation IP addresses hashed
- **Local Processing**: All LLM inference on-premise
- **Session Cleanup**: Auto-delete conversations after 90 days

### Authentication
- **Admin Panel**: Simple username/password (can upgrade to JWT later)
- **Widget**: No auth required (public-facing)

---

## 🔧 Technical Decisions Addressed

### 1. Ollama Model Selection

| Model | Params | Speed | Quality | Recommendation |
|-------|--------|-------|---------|----------------|
| **llama3.2** | 3B | Fast | Good | ✅ Primary (default) |
| **phi3.5** | 3.8B | Fast | Good | Alternative |
| **mistral** | 7B | Medium | Better | If GPU available |

**Decision**: Use `llama3.2` for MVP (fast, good quality, ~4GB VRAM). Can swap to `mistral` if accuracy issues.

### 2. Vector Database

| Option | Pros | Cons | Decision |
|--------|------|------|----------|
| **Chroma** | LangChain native, simple | Single-node | ✅ MVP |
| **FAISS** | Fast, no deps | No persistence | ❌ |
| **pgvector** | Production-grade | Requires Postgres | Phase 2 |

**Decision**: Chroma for MVP (simple, works with LangChain). Migrate to pgvector in Phase 2 for production.

### 3. Embeddable Widget Architecture

```javascript
// Option A: Script tag (recommended)
<script src="https://chatbot.example.com/widget.js" 
        data-city="kitchener" 
        data-primary-color="#006699"></script>

// Option B: iframe
<iframe src="https://chatbot.example.com/embed/kitchener" 
        width="400" height="600"></iframe>
```

**Decision**: Provide both. Script tag loads React widget dynamically; iframe is fallback for sites without JS.

### 4. Data Ingestion (RAG)

| Source | Method | Frequency |
|--------|--------|-----------|
| City website pages | Web scraper (BeautifulSoup) | Weekly cron |
| PDF documents | PDF parser (pymupdf) | On-demand |
| Open Data Portal | API fetch | Monthly |
| Manual Q&A | Admin UI | As needed |

**Decision**: Build `scripts/ingest.py` that reads `config/ingestion.json` for URL list. Run via cron or admin trigger.

---

## 📦 Infrastructure (Docker Compose)

```yaml
# docker-compose.yml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: municipal_chatbot
      POSTGRES_USER: chatbot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://chatbot:${DB_PASSWORD}@postgres:5432/municipal_chatbot
      - OLLAMA_BASE_URL=http://ollama:11434
    depends_on:
      - postgres
      - ollama

  frontend:
    build: ./frontend
    ports:
      - "3000:80"  # Nginx serves static

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - frontend
      - backend
```

---

## 📋 Implementation Steps (Ordered)

### Sprint 1: Foundation (Week 1-2)
1. **Replace OpenAI with Ollama** in existing `main.py` 
   - Add `langchain_ollama` imports
   - Change embeddings to `OllamaEmbeddings`
   - Change LLM to `Ollama` model
2. **Set up PostgreSQL** with Docker Compose
3. **Create SQLAlchemy models** matching schema above
4. **Build basic React widget** with chat UI

### Sprint 2: Core Chat (Week 2-3)
5. **Implement /chat endpoint** with RAG flow
6. **Add conversation logging** to PostgreSQL
7. **Implement source citations** (track source docs in response)
8. **Create embeddable script** for widget distribution

### Sprint 3: Polish (Week 3-4)
9. **Build admin dashboard** (analytics + CMS)
10. **Add feedback collection** (star ratings)
11. **Mobile responsive** CSS fixes
12. **Deploy to staging** (CI/CD pipeline)

---

## 🔎 Ticket Review

### Existing Tickets (from TICKETS.md) - ✅ Complete

| Ticket | Title | Assessment |
|--------|-------|------------|
| TICKET-001 | Set up Ollama with Local LLM | ✅ Required - already identified |
| TICKET-002 | Create Chat Widget Frontend Component | ✅ Valid |
| TICKET-003 | Build RAG Pipeline for City Content | ✅ Valid |
| TICKET-004 | Connect Chat Widget to Backend API | ✅ Valid |
| TICKET-005 | Implement Source Citations | ✅ Valid |
| TICKET-006 | Add Conversation Logging | ✅ Valid |
| TICKET-007 | Make Widget Responsive (Mobile) | ✅ Valid |
| TICKET-008 | Create Embeddable Script | ✅ Valid |
| TICKET-009 | Deploy to Staging Environment | ✅ Valid |
| TICKET-010 | Initial Q&A Knowledge Base | ✅ Valid |

### Missing Tickets Identified

| New Ticket | Title | Priority | Rationale |
|------------|-------|----------|-----------|
| TICKET-011 | Replace OpenAI with Ollama in Backend | P0 | Current code uses OpenAI - violates self-hosted requirement |
| TICKET-012 | Set Up PostgreSQL with Docker | P0 | No database infrastructure yet |
| TICKET-013 | Implement Rate Limiting | P1 | Security requirement not addressed in tickets |
| TICKET-014 | Create Admin Authentication | P1 | Admin panel needs basic auth |
| TICKET-015 | Build Embeddable Widget Loader | P0 | Required for TICKET-008 |
| TICKET-016 | Add Health Check with Ollama Status | P1 | Need to verify Ollama is running before queries |

---

## 📊 File Structure (Final)

```
municipal-chatbot/
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Environment template
├── backend/
│   ├── Dockerfile
│   ├── main.py                 # FastAPI app (REFACTOR to use Ollama)
│   ├── requirements.txt
│   ├── api/
│   │   ├── routes/
│   │   │   ├── chat.py
│   │   │   ├── admin.py
│   │   │   └── health.py
│   │   └── deps.py             # Shared dependencies
│   ├── rag/
│   │   ├── pipeline.py         # LangChain RAG logic
│   │   ├── ingest.py           # Content scraper
│   │   └── chroma_client.py    # Vector DB wrapper
│   ├── llm/
│   │   └── ollama_client.py    # Ollama wrapper
│   └── db/
│       ├── models.py           # SQLAlchemy models
│       └── migrations/         # Alembic migrations
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── widget/
│   │   ├── ChatWidget.tsx      # Main widget component
│   │   ├── ChatWindow.tsx      # Message display
│   │   ├── ChatInput.tsx       # User input
│   │   └── widget.tsx          # Entry point + mount
│   ├── dashboard/
│   │   ├── Analytics.tsx       # Charts + stats
│   │   └── ContentEditor.tsx   # Knowledge base editor
│   └── components/
│       ├── Button.tsx
│       ├── Input.tsx
│       └── Modal.tsx
├── scripts/
│   ├── ingest.py               # City content scraper
│   └── seed_db.py              # Sample Q&A data
├── config/
│   ├── cities.json             # City configurations
│   ├── ingestion.json          # URLs to scrape
│   └── ollama_models.json      # Model settings
└── nginx/
    └── nginx.conf              # Reverse proxy config
```

---

## ⚠️ Critical Notes for Dinesh

1. **Current backend uses OpenAI** - This must be replaced with Ollama before anything else. Priority #1.

2. **Ollama must be running before backend starts** - Add health check that pings Ollama before accepting requests.

3. **Use langchain-ollama** - The package is `langchain-ollama`, not the deprecated `langchain.llms.ollama`.

4. **Vector DB persistence** - Chroma DB must persist between restarts. Mount volume in Docker.

5. **Widget embed** - Keep it under 50KB. No heavy dependencies. Use Shadow DOM to isolate styles.

6. **Rate limiting** - Implement at Nginx level for simplicity, or use `slowapi` in FastAPI.

7. **Multi-city support** - Design tables with `city` column from the start. Don't add later.

---

*Architecture complete. Ready for Dinesh to begin implementation.*