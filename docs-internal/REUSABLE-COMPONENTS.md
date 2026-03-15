# Municipal Chatbot - Reusable Components & Architecture

**Project:** Municipal Chatbot for Kitchener/Waterloo Region  
**Purpose:** Document reusable elements for other municipalities

---

## 1. Frontend Libraries Selection

| Component | Library | Rationale |
|-----------|---------|-----------|
| **Chat Widget** | `react-chat-widget` or Custom React | Lightweight, easily embeddable |
| **UI Framework** | Tailwind CSS | Minimal footprint, easy theming |
| **Icons** | Lucide React | Open source, consistent style |
| **Markdown Rendering** | `react-markdown` | Clean answer formatting |
| **State Management** | React Context (no Redux needed) | Simple enough for MVP |

### Embeddable Widget Architecture
```javascript
// Standalone widget that can be embedded on any city website
<script src="https://cdn.municipalchatbot.ca/widget.js"></script>
<script>
  MunicipalChatbot.init({
    city: 'kitchener',
    primaryColor: '#006699',
    position: 'bottom-right'
  });
</script>
```

---

## 2. Backend Reusable Components

### 2.1 RAG Pipeline (LangChain-based)
- **Location**: `backend/rag/`
- **Purpose**: Ingest any municipality's website content into vector DB
- **Config**: JSON file defining URLs to scrape, update frequency

### 2.2 LLM Interface (Ollama)
- **Location**: `backend/llm/`
- **Purpose**: Abstraction layer for local LLM inference
- **Model**: llama3.2 (or smaller for speed)
- **Benefit**: Swap Ollama for other backends without code changes

### 2.3 Conversation Storage
- **Location**: `backend/db/`
- **Database**: SQLite (MVP) → PostgreSQL (production)
- **Tables**: conversations, messages, feedback, knowledge_base

---

## 3. Data Schema (Reusable)

```sql
-- knowledge_base: Q&A content managed by admins
CREATE TABLE knowledge_base (
  id SERIAL PRIMARY KEY,
  category VARCHAR(50),  -- 'garbage', 'parking', 'permits'
  question TEXT NOT NULL,
  answer TEXT NOT NULL,
  sources JSONB,         -- [{url, title}]
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- conversations: Log all user interactions
CREATE TABLE conversations (
  id SERIAL PRIMARY KEY,
  session_id VARCHAR(100),
  city VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- messages: Individual messages in a conversation
CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  conversation_id INTEGER REFERENCES conversations(id),
  role VARCHAR(10),      -- 'user' or 'assistant'
  content TEXT,
  sources JSONB,
  response_time_ms INTEGER,
  rating INTEGER         -- 1-5, nullable
);
```

---

## 4. Adapting for Other Municipalities

### Step-by-Step Guide

1. **Deploy Backend**
   ```bash
   docker-compose up -d
   ```

2. **Configure City**
   - Add city config to `config/cities.json`:
   ```json
   {
     "city": "guelph",
     "name": "City of Guelph",
     "primaryColor": "#FF6600",
     "websites": [
       "https://guelph.ca/...",
       "https://guelph.ca/bylaw/"
     ]
   }
   ```

3. **Run RAG Pipeline**
   ```bash
   npm run ingest -- --city=guelph
   ```

4. **Deploy Widget**
   ```bash
   # Embed on city website
   <script src="https://chatbotcdn.ca/widget.js"
     data-city="guelph"
     data-color="#FF6600">
   </script>
   ```

---

## 5. Cost Estimates (Per Municipality)

| Item | Monthly Cost |
|------|--------------|
| Hosting (VPS $20/mo) | $20 |
| Ollama GPU (shared) | $0-50 |
| Domain/SSL | $10 |
| **Total** | **$30-80/month** |

---

## 6. Key Files Structure

```
municipal-chatbot/
├── frontend/
│   ├── widget/           # Embeddable chat widget
│   ├── dashboard/        # Admin panel (Phase 2)
│   └── components/       # Shared UI components
├── backend/
│   ├── api/              # FastAPI endpoints
│   ├── rag/              # RAG pipeline
│   ├── llm/              # Ollama integration
│   └── db/               # Database models
├── config/
│   └── cities.json       # Multi-city config
├── scripts/
│   ├── ingest.js         # Content scraping
│   └── deploy.sh         # Deployment automation
└── docker-compose.yml    # One-command deployment
```

---

## 7. Competitive Differentiation

| Feature | Our Solution | municiPal AI | CivicPlus |
|---------|--------------|--------------|-----------|
| **Hosting** | Self-hosted | Cloud | Cloud |
| **LLM** | Local (Ollama) | External API | External API |
| **Cost** | $30-80/mo | $500+/mo | $1000+/mo |
| **Customization** | Full source | Limited | Limited |
| **Setup Time** | 1 day | 1 week | 2 weeks |

---

## 8. Scalability Path

1. **MVP**: Single city, SQLite, single Ollama instance
2. **Phase 2**: Add admin dashboard, PostgreSQL
3. **Phase 3**: Multi-city with city-specific knowledge bases
4. **Future**: Federated deployment (Region-wide, multiple municipalities)

---

*This architecture is designed for municipalities with limited IT budgets. The self-hosted, open-source approach minimizes licensing costs and gives cities full control over their data.*