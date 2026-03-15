# Municipal Chatbot MVP — Code Review Report

**Reviewer:** Monica (Code Quality Gate)  
**Date:** 2025-01-20  
**Build Status:** Bug fix applied for embeddings import scoping

---

## 📋 Quality Gate Executive Summary

| | |
|---|---|
| **Release Readiness** | 🔄 **CONDITIONAL GO** — Several security and reliability issues need attention before production |
| **Key Quality Risks** | 1. Widget not calling backend API (demo-only mode) <br>2. No input validation on email fields <br>3. Global mutable state not thread-safe |
| **Recommended Actions** | 1. Wire up widget to actual backend API <br>2. Add email format validation <br>3. Fix CORS for production <br>4. Add session expiration |

---

## 🔍 Code & Security Assessment

### Logic Review

| Component | Status | Notes |
|-----------|--------|-------|
| **Backend (main.py)** | ✅ Good | FastAPI structure is solid. RAG pipeline correctly implemented with fallback chain (Ollama → HuggingFace → MockLLM). |
| **Database (database.py)** | ✅ Good | Parameterized queries prevent SQL injection. Proper indexes on session_id and messages. |
| **Email Service** | ✅ Good | SMTP credentials via environment variables. Graceful fallback when not configured. |
| **Frontend (React)** | ⚠️ Fair | Clean Zustand store, but API endpoint path mismatch (`/api/chat` vs backend `/chat`). |
| **Widget** | 🔴 Weak | **Only uses demo responses** — does not call backend API. Purely cosmetic. |

### Security Validation

| Issue | Severity | Status |
|-------|----------|--------|
| **SQL Injection** | Critical | ✅ Fixed — All queries use parameterized placeholders |
| **Secret Management** | High | ✅ Safe — `.env` not committed; credentials via `os.getenv()` |
| **Input Validation** | Medium | ⚠️ Missing — No email format validation in `create_session` endpoint |
| **CORS Configuration** | Medium | ⚠️ Risk — Default `CORS_ORIGINS="*"` allows any origin |
| **XSS in Widget** | Low | ✅ Protected — Uses `escapeHTML()` function |
| **Rate Limiting** | Medium | ❌ Missing — No protection against abuse |
| **Session Expiration** | Low | ⚠️ Missing — Sessions never expire |

---

## ✅ Requirements Checklist

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Session capture (name/email) | `/api/session` endpoint + WelcomeScreen | ✅ Complete |
| Email summary on session end | `email_service.send_conversation_summary()` | ✅ Complete |
| Chat functionality | `/chat` endpoint + React UI | ✅ Complete |
| Embeddable widget | `widget/municipal-chat.js` | ⚠️ Incomplete (demo only) |

---

## 🎯 Critical Issues (Must Fix)

### 1. Widget Not Connected to Backend
**File:** `widget/municipal-chat.js`  
**Problem:** Widget uses hardcoded `DEMO_RESPONSES` and never calls the backend API. The `sendMessage()` function just does a `setTimeout` and returns demo text.  
**Impact:** Users cannot get real AI responses. Widget is non-functional for production.  
**Fix:** Replace `DEMO_RESPONSES` logic with actual `fetch()` call to backend `/chat` endpoint.

### 2. No Email Validation
**File:** `backend/main.py` — `CreateSessionRequest`  
**Problem:** Email field accepts any string. Malformed emails could cause issues downstream.  
**Impact:** Database may contain invalid emails; email summary delivery fails silently.  
**Fix:** Add Pydantic `EmailStr` validation:
```python
from pydantic import EmailStr

class CreateSessionRequest(BaseModel):
    name: str
    email: Optional[EmailStr] = None  # Add validation
```

### 3. CORS Wide Open
**File:** `backend/main.py`  
**Problem:** Default `CORS_ORIGINS="*"` in production could allow unauthorized cross-site requests.  
**Fix:** Require explicit CORS_ORIGINS in `.env` for production; reject "*" in production mode.

---

## 💡 Suggestions (Nice to Have)

### 1. Add Rate Limiting
Protect the `/chat` endpoint from abuse using `fastapi-limiter` or similar.

### 2. Session Expiration
Add TTL to sessions (e.g., 24 hours) to prevent database bloat:
```python
# In database.py get_session()
cursor.execute("""
    SELECT * FROM sessions 
    WHERE session_id = ? AND started_at > datetime('now', '-24 hours')
""", (session_id,))
```

### 3. Thread-Safe Global State
The global `embeddings`, `vectorstore`, and `llm` objects could cause race conditions. Consider using `FastAPI`'s lifespan events or a connection pool.

### 4. API Path Mismatch
Frontend calls `/api/chat` but backend serves `/chat`. Fix in `frontend/src/api/chat.ts`:
```typescript
// Change from '/api/chat' to '/chat'
const response = await fetch(`${API_BASE}/chat`, {...})
```

### 5. Health Check Enhancement
Add timestamp to health check response for monitoring stale connections.

---

## 📊 Summary

| Category | Score |
|----------|-------|
| Security | 7/10 |
| Code Quality | 8/10 |
| Error Handling | 7/10 |
| Performance | 7/10 |
| Requirements Met | 85% |

**Verdict:** 🔄 **Changes Requested**

The core RAG pipeline and backend are solid. The main gaps are:
1. Widget needs backend integration (critical)
2. Input validation gaps (medium)
3. Production hardening (CORS, rate limiting)

**Next Step:** Hand off to Dinesh (Coder) to fix issues #1-3 above, then re-review before QA.