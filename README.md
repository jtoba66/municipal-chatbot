# Municipal Chatbot

AI-powered citizen assistance chatbot for Kitchener/Waterloo region. Built with FastAPI, React, and Ollama for local LLM inference.

## Features

- 🤖 AI-powered chat with municipal information
- 📚 RAG (Retrieval-Augmented Generation) for accurate answers
- 💬 Clean chat UI with typing indicators
- 📧 Session capture with email summaries
- 🔒 Privacy-focused (runs locally with Ollama)
- 🐳 Docker-ready deployment

## Quick Start

### Prerequisites

- Docker & Docker Compose
- OR Python 3.11+ with Ollama installed

### Using Docker

```bash
# Clone and run
docker-compose up -d

# Access
# Frontend: http://localhost:3001
# Backend: http://localhost:8000
```

### Local Development

**Backend:**
```bash
cd backend
cp .env.example .env
# Add your OpenRouter API key to .env
pip install -r requirements.txt
python main.py
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
municipal-chatbot/
├── backend/          # FastAPI + SQLite + RAG
├── frontend/         # React + Tailwind
├── widget/           # Embeddable chat widget
├── nginx/            # Reverse proxy config
├── data/             # Knowledge base (see README)
├── docker-compose.yml
└── README.md
```

## Knowledge Base

The chatbot uses RAG to answer questions about:
- Garbage & recycling schedules
- Parking rules & permits
- Property taxes
- Bylaws & contact info

See `data/documents/README.md` to set up your own city's data.

## Tech Stack

- **Backend:** FastAPI, LangChain, ChromaDB, Ollama
- **Frontend:** React, TailwindCSS, TypeScript
- **Database:** SQLite
- **LLM:** Ollama (Llama 3.2) or OpenRouter

## License

MIT