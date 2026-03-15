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

## 🤖 Agentic Actions Architecture

This section defines the architecture for **Agentic Actions** — enabling citizens to complete municipal tasks (report issues, book permits, pay tickets) directly through the chatbot by automating form submission via Playwright.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        AGENTIC ACTIONS SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────────┐     ┌──────────────────────┐  │
│  │  User Input  │────▶│  Intent Detector │────▶│  Action Classifier   │  │
│  │   (Message)  │     │     (LLM)        │     │     (LLM)            │  │
│  └──────────────┘     └──────────────────┘     └──────────┬───────────┘  │
│                                                            │               │
│                         ┌──────────────────────────────────┘               │
│                         ▼                                                      │
│              ┌─────────────────────┐                                        │
│              │   Action State      │                                        │
│              │     Machine         │                                        │
│              └──────────┬──────────┘                                        │
│                         │                                                    │
│         ┌───────────────┼───────────────┐                                  │
│         ▼               ▼               ▼                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                          │
│  │  COLLECTING │ │ CONFIRMING  │ │ EXECUTING   │                          │
│  │  (Fields)   │ │  (Review)   │ │  (Action)   │                          │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘                          │
│         │               │               │                                  │
│         │               │               ▼                                  │
│         │               │      ┌─────────────────┐                         │
│         │               │      │  Action Runner  │                         │
│         │               │      │   (Playwright)  │                         │
│         │               │      └────────┬────────┘                         │
│         │               │               │                                  │
│         │               │               ▼                                  │
│         │               │      ┌─────────────────┐                         │
│         │               │      │  City Portal    │                         │
│         │               │      │  (External)     │                         │
│         │               │      └─────────────────┘                         │
│         │               │                                                    │
│         │               │               │                                  │
│         ▼               ▼               ▼                                  │
│         │               │               │                                  │
│         └───────────────┼───────────────┘                                  │
│                         ▼                                                  │
│              ┌─────────────────────┐                                        │
│              │   Display Result    │                                        │
│              │    to User          │                                        │
│              └─────────────────────┘                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 1. Intent Detection System

The system uses the LLM to classify every user message as either a **question** (answer with RAG) or an **action request** (initiate agentic action).

#### 1.1 Classification Prompt

```python
ACTION_CLASSIFICATION_PROMPT = """Classify this municipal chatbot message.

Message: "{message}"

Options:
- QUESTION: User wants information, answer, or explanation
- ACTION_REQUEST: User wants to DO something (report issue, book, pay, submit form)

If the user wants to report a problem, book something, pay for something, submit something, 
or complete a transaction, it's an ACTION_REQUEST.
Otherwise, it's a QUESTION.

Return ONLY valid JSON:
{{"classification": "QUESTION"}}
OR
{{"classification": "ACTION_REQUEST", "action_type": "report_pothole|parking_permit|pay_ticket|...", "fields_found": {{"field_name": "value"}}}}
"""

def classify_message(message: str) -> dict:
    """Classify message as question or action request."""
    llm = get_llm()
    response = llm.invoke(ACTION_CLASSIFICATION_PROMPT.format(message=message))
    # Parse JSON response
    return json.loads(response.content)
```

#### 1.2 Action Schema Definition

Each action defines its required fields and validation rules:

```python
ACTION_SCHEMAS = {
    "report_pothole": {
        "required_fields": ["issue_type", "location", "description", "contact_name"],
        "optional_fields": ["photo"],
        "field_prompts": {
            "issue_type": "What type of issue is this? (Options: Graffiti, Illegal sign, Litter, Pothole, Sidewalk hazard, Other)",
            "location": "What is the location of the issue? (Street address or intersection)",
            "description": "Please describe the issue in detail:",
            "contact_name": "What is your contact name?"
        },
        "validation": {
            "location": r"^\d+.*[a-zA-Z]",  # Must have number + street name
            "contact_name": r"^.{2,}$"       # At least 2 characters
        }
    },
    "parking_permit": {
        "required_fields": ["preferred_location", "email", "license_plate", "phone"],
        "optional_fields": [],
        "field_prompts": {
            "preferred_location": "Which parking location would you like? (Options: Queen Street South, Charles Street West, Transit, etc.)",
            "email": "What is your email address?",
            "license_plate": "What is your vehicle's license plate number?",
            "phone": "What is your phone number?"
        },
        "validation": {
            "email": r"^[^@]+@[^@]+\.[^@]+$",
            "license_plate": r"^[A-Z0-9]{2,8}$",
            "phone": r"^\d{10}$"
        }
    },
    "pay_ticket": {
        "required_fields": ["ticket_number"],
        "optional_fields": [],
        "field_prompts": {
            "ticket_number": "What is your ticket number?"
        },
        "validation": {
            "ticket_number": r"^\d{6,8}$"
        }
    }
}
```

---

### 2. Field Collection Flow

#### 2.1 State Machine

The system tracks action progress using a state machine:

```
        ┌─────────────────────────────────────────────────────────┐
        │                                                         │
        ▼                                                         │
    IDLE ──────────────────────────────────────────────▶ (end)   │
        │                                                         │
        │ User triggers action                                    │
        ▼                                                         │
  COLLECTING ◀──────────────────────────────────────┐            │
        │                                          │            │
        │ All fields collected                      │ User       │
        ▼                                          │ provides   │
  CONFIRMING ◀─────────────────────────────────────┘ answer     │
        │                                                         │
        │ User confirms (Yes)                                     │
        ▼                                                         │
   EXECUTING ─────────────────┐                                  │
        │                      │                                  │
        │ Action completes     │ Action fails                     │
        ▼                      ▼                                  │
   COMPLETE              TRY_AGAIN ◀──────────────────────────────┘
        │                      │                                  │
        │                      │ Max 3 retries                    │
        └──────────────────────┘                                  │
        │                                                         │
        ▼                                                         │
    (end)                                                        │
```

#### 2.2 Session State Storage

```python
# Database table for pending action state
# Stored in PostgreSQL to survive restarts

class ActionState:
    """Tracks in-progress action for a session."""
    session_id: str              # References conversations.session_id
    action_type: str             # e.g., "report_pothole"
    state: str                   # IDLE | COLLECTING | CONFIRMING | EXECUTING | COMPLETE
    current_field: str           # Field being collected (None if confirming)
    fields_gathered: JSONB       # {"issue_type": "Pothole", "location": "..."}
    retry_count: int             # For failed action executions
    created_at: datetime
    updated_at: datetime

# SQLAlchemy model
class ActionStateModel(Base):
    __tablename__ = "action_states"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), ForeignKey("conversations.session_id"))
    action_type = Column(String(50))
    state = Column(String(20), default="IDLE")
    current_field = Column(String(50))
    fields_gathered = Column(JSONB, default={})
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### 2.3 Field Collection Logic

```python
async def collect_field(session_id: str, user_response: str) -> dict:
    """
    Process user's response for the current field being collected.
    Returns the next state and response to display to user.
    """
    # Get current action state
    action_state = get_action_state(session_id)
    
    # Validate the response against current field's validation rules
    schema = ACTION_SCHEMAS[action_state.action_type]
    field_name = action_state.current_field
    validation_rule = schema["validation"].get(field_name)
    
    if validation_rule:
        if not re.match(validation_rule, user_response):
            return {
                "state": "COLLECTING",
                "message": f"Invalid format for {field_name}. Please try again.",
                "current_field": field_name
            }
    
    # Save validated field
    action_state.fields_gathered[field_name] = user_response
    
    # Find next missing field
    required_fields = schema["required_fields"]
    gathered = action_state.fields_gathered
    next_field = None
    
    for field in required_fields:
        if field not in gathered or not gathered[field]:
            next_field = field
            break
    
    if next_field:
        # Continue collecting
        action_state.current_field = next_field
        action_state.state = "COLLECTING"
        save_action_state(action_state)
        
        return {
            "state": "COLLECTING",
            "message": schema["field_prompts"][next_field],
            "current_field": next_field
        }
    else:
        # All fields collected - move to confirmation
        action_state.state = "CONFIRMING"
        action_state.current_field = None
        save_action_state(action_state)
        
        return build_confirmation_message(action_state)
```

---

### 3. Action Execution Layer

#### 3.1 Action Module Structure

```
backend/
├── actions/
│   ├── __init__.py
│   ├── base.py           # Base action class
│   ├── report_pothole.py # Issue reporting action
│   ├── parking_permit.py # Permit booking action
│   ├── pay_ticket.py     # Ticket payment action
│   └── runner.py         # Action execution coordinator
```

#### 3.2 Base Action Class

```python
# backend/actions/base.py
from abc import ABC, abstractmethod
from typing import Optional
from pydantic import BaseModel

class ActionResult(BaseModel):
    success: bool
    confirmation_number: Optional[str] = None
    message: str
    retry_possible: bool = True

class BaseAction(ABC):
    """Base class for all agentic actions."""
    
    name: str  # e.g., "report_pothole"
    required_fields: list[str]
    
    @abstractmethod
    async def execute(self, fields: dict) -> ActionResult:
        """Execute the action with collected fields."""
        pass
    
    @abstractmethod
    def get_portal_url(self) -> str:
        """Return the URL of the form to submit."""
        pass
    
    async def validate_fields(self, fields: dict) -> tuple[bool, str]:
        """Validate all fields before execution."""
        for field in self.required_fields:
            if not fields.get(field):
                return False, f"Missing required field: {field}"
        return True, ""
```

#### 3.3 Example Action Implementation (Playwright)

```python
# backend/actions/report_pothole.py
from playwright.async_api import async_playwright
from .base import BaseAction, ActionResult

class ReportPotholeAction(BaseAction):
    name = "report_pothole"
    required_fields = ["issue_type", "location", "description", "contact_name"]
    
    def get_portal_url(self) -> str:
        return "https://form.kitchener.ca/CSD/CCS/Report-a-problem"
    
    async def execute(self, fields: dict) -> ActionResult:
        """Submit issue report via Playwright."""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                # Navigate to form
                await page.goto(self.get_portal_url())
                
                # Select issue type from dropdown
                await page.select_option(
                    'select[name="issueType"]',
                    fields["issue_type"]
                )
                
                # Fill location
                await page.fill('input[name="location"]', fields["location"])
                
                # Fill description
                await page.fill('textarea[name="description"]', fields["description"])
                
                # Fill contact info
                await page.fill('input[name="contactName"]', fields["contact_name"])
                
                # Submit form
                await page.click('button[type="submit"]')
                
                # Wait for confirmation
                await page.wait_for_selector(".confirmation-number", timeout=10000)
                confirmation = await page.text_content(".confirmation-number")
                
                return ActionResult(
                    success=True,
                    confirmation_number=confirmation,
                    message=f"Report submitted successfully! Confirmation: {confirmation}"
                )
                
            except Exception as e:
                return ActionResult(
                    success=False,
                    message=f"Failed to submit report: {str(e)}",
                    retry_possible=True
                )
            finally:
                await browser.close()
```

#### 3.4 Input Validation Before Execution

```python
# backend/actions/runner.py
async def execute_action(action_type: str, fields: dict) -> ActionResult:
    """
    Execute an action with full validation and error handling.
    """
    # 1. Validate all required fields present
    schema = ACTION_SCHEMAS[action_type]
    for field in schema["required_fields"]:
        if not fields.get(field):
            return ActionResult(
                success=False,
                message=f"Missing required field: {field}",
                retry_possible=False
            )
    
    # 2. Validate field formats
    for field, value in fields.items():
        if field in schema["validation"]:
            pattern = schema["validation"][field]
            if not re.match(pattern, str(value)):
                return ActionResult(
                    success=False,
                    message=f"Invalid format for {field}: {value}",
                    retry_possible=False
                )
    
    # 3. Execute the action
    action_class = ACTION_REGISTRY.get(action_type)
    if not action_class:
        return ActionResult(
            success=False,
            message=f"Unknown action type: {action_type}",
            retry_possible=False
        )
    
    action = action_class()
    return await action.execute(fields)
```

---

### 4. Frontend Changes

#### 4.1 Confirmation Dialog Design

When the state transitions to `CONFIRMING`, the frontend displays a structured confirmation:

```tsx
// frontend/src/components/ActionConfirmation.tsx
interface ActionConfirmationProps {
  actionType: string;
  fields: Record<string, string>;
  onConfirm: () => void;
  onCancel: () => void;
  onEditField: (field: string) => void;
}

export function ActionConfirmation({ 
  actionType, 
  fields, 
  onConfirm, 
  onCancel, 
  onEditField 
}: ActionConfirmationProps) {
  const actionLabels = {
    report_pothole: "Report Issue",
    parking_permit: "Book Parking Permit",
    pay_ticket: "Pay Parking Ticket"
  };
  
  return (
    <div className="action-confirmation">
      <h3>Confirm Your {actionLabels[actionType]}</h3>
      <p className="disclaimer">
        I will submit this information to the City of Kitchener on your behalf.
      </p>
      
      <div className="fields-summary">
        {Object.entries(fields).map(([key, value]) => (
          <div key={key} className="field-row">
            <span className="field-label">{formatLabel(key)}:</span>
            <span className="field-value">{value}</span>
            <button onClick={() => onEditField(key)} className="edit-btn">
              Edit
            </button>
          </div>
        ))}
      </div>
      
      <div className="confirmation-buttons">
        <button onClick={onCancel} className="btn-cancel">
          Cancel
        </button>
        <button onClick={onConfirm} className="btn-confirm">
          Yes, Submit
        </button>
      </div>
    </div>
  );
}
```

#### 4.2 Status Display States

```tsx
// Execution status states
type ExecutionStatus = 'idle' | 'executing' | 'success' | 'partial_success' | 'failure';

function ActionStatusDisplay({ status, result }: { 
  status: ExecutionStatus; 
  result?: ActionResult 
}) {
  const statusContent = {
    executing: {
      icon: "⏳",
      message: "Submitting your request..."
    },
    success: {
      icon: "✅",
      message: result?.confirmation_number 
        ? `Request submitted! Confirmation: ${result.confirmation_number}`
        : "Request submitted successfully!"
    },
    partial_success: {
      icon: "⚠️",
      message: "Request submitted but couldn't get confirmation number. " +
        "Please save your session ID and contact 519-741-2345 if needed."
    },
    failure: {
      icon: "❌",
      message: "Unable to complete your request. " +
        "Would you like me to open the form in a new tab?"
    }
  };
  
  return (
    <div className={`status-display ${status}`}>
      <span className="icon">{statusContent[status].icon}</span>
      <span className="message">{statusContent[status].message}</span>
    </div>
  );
}
```

---

### 5. API Endpoint Design

#### 5.1 New Endpoints

```
# Action Classification (classify message as question vs action)
POST /api/actions/classify
Body: { "message": "I want to report a pothole" }
Response: { 
  "classification": "ACTION_REQUEST", 
  "action_type": "report_pothole", 
  "fields_found": { "location": "King Street" }
}

# Get action schema (for field prompts)
GET /api/actions/{action_type}/schema
Response: {
  "required_fields": ["issue_type", "location", "description", "contact_name"],
  "field_prompts": { ... }
}

# Submit field answer during collection
POST /api/actions/{action_type}/field
Body: { "session_id": "...", "field": "location", "value": "123 Main St" }
Response: { 
  "state": "COLLECTING", 
  "next_field": "description",
  "prompt": "Please describe the issue in detail:"
}

# Confirm and execute action
POST /api/actions/{action_type}/execute
Body: { "session_id": "...", "confirmed": true }
Response: { 
  "status": "executing",
  "message": "Submitting your request..."
}

# Poll for execution result
GET /api/actions/{action_type}/result?session_id=...
Response: {
  "status": "success" | "failure",
  "confirmation_number": "ABC123",
  "message": "..."
}
```

#### 5.2 Backend Route Implementation

```python
# backend/main.py additions

@app.post("/api/actions/classify")
async def classify_message(request: ClassifyRequest):
    """Classify message as question or action request."""
    result = await classify_intent(request.message)
    return result

@app.post("/api/actions/{action_type}/field")
async def submit_field(
    action_type: str, 
    request: FieldSubmitRequest
):
    """Submit a field value during field collection."""
    return await collect_field(request.session_id, request.field, request.value)

@app.post("/api/actions/{action_type}/execute")
async def execute_action(
    action_type: str,
    request: ExecuteRequest
):
    """Execute the action after user confirmation."""
    action_state = get_action_state(request.session_id)
    
    if not request.confirmed:
        # User declined - reset to IDLE
        clear_action_state(request.session_id)
        return {"status": "cancelled", "message": "Action cancelled."}
    
    # Execute the action
    action_state.state = "EXECUTING"
    save_action_state(action_state)
    
    # Run in background
    result = await execute_action_async(action_type, action_state.fields_gathered)
    
    # Update state based on result
    if result.success:
        action_state.state = "COMPLETE"
    else:
        action_state.retry_count += 1
        action_state.state = "TRY_AGAIN" if action_state.retry_count < 3 else "COMPLETE"
    
    save_action_state(action_state)
    
    return {
        "status": "executing",
        "message": result.message
    }

async def execute_action_async(action_type: str, fields: dict) -> ActionResult:
    """Execute action in background."""
    return await runner.execute_action(action_type, fields)
```

---

### 6. Database Schema Changes

```sql
-- New table: Action states (tracks in-progress actions)
CREATE TABLE action_states (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL REFERENCES conversations(session_id),
    action_type VARCHAR(50) NOT NULL,
    state VARCHAR(20) NOT NULL DEFAULT 'IDLE',
    current_field VARCHAR(50),
    fields_gathered JSONB DEFAULT '{}',
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_action_state_session ON action_states(session_id);
CREATE INDEX idx_action_state_state ON action_states(state);

-- New table: Action history (for analytics)
CREATE TABLE action_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) REFERENCES conversations(session_id),
    action_type VARCHAR(50) NOT NULL,
    fields_submitted JSONB,
    confirmation_number VARCHAR(100),
    status VARCHAR(20) NOT NULL,  -- 'success', 'failure', 'cancelled'
    error_message TEXT,
    executed_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_action_history_type ON action_history(action_type);
CREATE INDEX idx_action_history_status ON action_history(status);
```

---

### 7. File Structure for Actions

```
backend/
├── main.py                    # [MODIFIED] Add action endpoints
├── actions/
│   ├── __init__.py
│   ├── base.py               # BaseAction class
│   ├── runner.py             # Action execution coordinator
│   ├── schemas.py            # ACTION_SCHEMAS dict
│   ├── report_issue.py       # 311 issue reporting
│   ├── parking_permit.py     # Parking permit booking
│   └── pay_ticket.py         # Ticket payment
├── db/
│   └── models.py             # [MODIFIED] Add ActionState, ActionHistory
└── services/
    └── playwright_service.py # Shared Playwright setup

frontend/src/
├── components/
│   ├── ActionConfirmation.tsx   # NEW - Confirmation dialog
│   ├── ActionStatus.tsx         # NEW - Status display
│   └── ChatWindow.tsx           # [MODIFIED] Handle action states
├── hooks/
│   └── useActionState.ts        # NEW - Action state management
└── api/
    └── actions.ts               # NEW - Action API client
```

---

### 8. Security Considerations

#### 8.1 Rate Limiting

```python
# Apply rate limiting specifically to action endpoints
from fastapi_limiter import Limiter
from fastapi_limiter.depends import RateLimiter

# Stricter limits for actions than for questions
action_limiter = RateLimiter(
    times=5,          # 5 actions per
    minutes=60,       # hour per IP
    identifier=lambda request: request.client.host
)

@app.post("/api/actions/{action_type}/execute")
@limiter.limit("5/minute", key_func=action_limiter)
async def execute_action(...):
    ...
```

#### 8.2 Input Sanitization

```python
def sanitize_action_input(value: str) -> str:
    """Sanitize user input for action fields."""
    # Remove any HTML/script tags
    value = re.sub(r'<[^>]*>', '', value)
    # Remove SQL injection patterns
    value = re.sub(r'(union|select|insert|delete|drop)', '', value, flags=re.I)
    # Limit length
    value = value[:500]
    return value.strip()
```

#### 8.3 Error Handling

```python
async def safe_execute_action(action_type: str, fields: dict) -> ActionResult:
    """Execute action with comprehensive error handling."""
    try:
        return await runner.execute_action(action_type, fields)
    except PlaywrightTimeoutError:
        return ActionResult(
            success=False,
            message="The city's form timed out. Please try again or use the direct link.",
            retry_possible=True
        )
    except PortalUnavailableError:
        return ActionResult(
            success=False,
            message="The city's portal is currently unavailable. Would you like me to open the form directly?",
            retry_possible=True
        )
    except Exception as e:
        # Log full error, return generic message
        logger.error(f"Action execution failed: {e}", exc_info=True)
        return ActionResult(
            success=False,
            message="An unexpected error occurred. Please try again later.",
            retry_possible=False  # Don't retry unknown errors
        )
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