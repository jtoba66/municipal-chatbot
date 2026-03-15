# Municipal Chatbot - Product Roadmap

**Project:** Municipal Chatbot for Kitchener/Waterloo Region  
**Version:** 1.0  
**Last Updated:** March 2025

---

## 🎯 Vision

A self-hosted, open-source AI chatbot that answers Waterloo Region citizens' municipal questions instantly—reducing 311 call volume, improving citizen satisfaction, and saving taxpayer money.

---

## 🚀 Phase 1: MVP (Weeks 1-4)

**Goal:** Get a working chatbot on city websites with basic Q&A capability.

### Features
| Feature | Description | Priority |
|---------|-------------|----------|
| **Chat Widget** | Embeddable React component for city websites | P0 |
| **RAG Pipeline** | Ingest city website content + Open Data Portal | P0 |
| **Local LLM** | Ollama with llama3.2 for inference | P0 |
| **Basic Q&A** | Answer garbage, parking, permit questions | P0 |
| **Source Citations** | Show source links for each answer | P1 |
| **Responsive UI** | Mobile-friendly chat interface | P1 |

### Success Criteria
- ✅ Chatbot deployed on test URL
- ✅ Can answer top 50 municipal questions
- ✅ Response time <3 seconds
- ✅ Works offline (local inference)

---

## 📦 Phase 2: Enhanced Capabilities (Weeks 5-8)

**Goal:** Add admin features and improve accuracy.

### Features
| Feature | Description | Priority |
|---------|-------------|----------|
| **Admin Dashboard** | View conversation analytics | P1 |
| **Content CMS** | Non-technical staff can update Q&A | P1 |
| **Feedback Collection** | User satisfaction ratings | P1 |
| **Human Handoff** | Escalate complex queries to email/311 | P2 |
| **Conversation History** | Users see previous messages | P2 |
| **Basic Logging** | Store conversations for analysis | P1 |

### Success Criteria
- ✅ City staff can update content without code
- ✅ Analytics show top query topics
- ✅ ≥4.0/5.0 user satisfaction

---

## 🌟 Phase 3: Scale & Polish (Weeks 9-12)

**Goal:** Multi-language support, production hardening, first city deployment.

### Features
| Feature | Description | Priority |
|---------|-------------|----------|
| **French Support** | bilingual Q&A (EN/FR) | P2 |
| **Production Deployment** | Deploy to first city (Kitchener pilot) | P1 |
| **Performance Optimization** | Caching, model tuning | P1 |
| **Error Handling** | Graceful degradation when LLM fails | P1 |
| **Multi-channel** | Also available as standalone page | P2 |
| **User Authentication** | Optional login for personalized answers | P3 |

---

## 🤖 Agentic Actions (Weeks 10-14)

**Goal:** Allow citizens to complete municipal tasks (report issues, book permits, pay tickets) directly through the chatbot via Playwright automation.

### Research Complete ✅
- LLM intent detection tested and working (see `llm-intent-test.md`)
- City portal field requirements documented (see `agentic-actions-research.md`)
- Detailed implementation plan available (see `AGENTIC-ACTIONS-PLAN.md`)

### Features
| Feature | Description | Priority |
|---------|-------------|----------|
| **Intent Detection** | Classify messages as QUESTION vs ACTION_REQUEST | P0 |
| **Field Collection Engine** | Ask user for missing fields, validate input | P0 |
| **Confirmation Dialog** | Show review summary before form submission | P0 |
| **Pay Parking Ticket (Kitchener)** | Automated ticket payment via GTechna portal | P1 |
| **Report Issue (Kitchener)** | Submit 311 service requests via form | P1 |
| **Book Parking Permit** | Fill parking permit application | P2 |
| **Check Permit Status** | Scrape permit status from portal | P2 |
| **Schedule Inspection** | Book building inspection slot | P2 |
| **Waterloo Support** | Extend actions to Waterloo city portals | P2 |

### Success Criteria
- ✅ ≥70% action completion rate
- ✅ <20% field collection abandonment
- ✅ ≥85% automation success on first attempt

### User Flow
```
User expresses intent → LLM detects ACTION_REQUEST → Collect missing fields → 
Review summary → User confirms → Execute via Playwright → Show result
```

### Priority Order
1. **Pay Parking Ticket** — Simplest (1-2 fields, external payment)
2. **Report Issue** — Simple form, good test case
3. **Book Parking Permit** — More fields, straightforward
4. **Check Permit Status** — Read-only, just scraping
5. **Schedule Inspection** — Most complex (permit validation + scheduling)

### Success Criteria
- ✅ Live on Kitchener or Waterloo city website
- ✅ 1,000+ conversations/month
- ✅ Cost per conversation <$0.05

---

## 🔭 Future (Post-MVP)

- **Voice Interface**: Phone-based chatbot (IVR integration)
- **Multi-city Federation**: Single admin panel for Region-wide deployment
- **Action Integration**: Allow users to pay tickets, book permits through chat
- **AI Agent**: More advanced automation (fill forms, track requests)
- **Other Municipalities**: Expand to Cambridge, Guelph, other Ontario cities

---

## 📊 Roadmap Visual

```
Q1 2025          Q2 2025          Q3 2025
─────────────────────────────────────────────────────
Phase 1 ████████
Phase 2     ████████████
Phase 3             ████████████████
                         ↑
                    First Live
                    Deployment
```

---

## ⚠️ Key Dependencies

1. **Week 1-2**: Need Ollama setup + local model selection (Gilfoyle)
2. **Week 2-3**: Need city website content for RAG ingestion (data gathering)
3. **Week 4**: Need first city partner for pilot feedback (Nicole Amaral outreach)
4. **Week 6**: Need hosting infrastructure (John/DevOps)

---

## Trade-off Decisions

| Decision | Rationale |
|----------|-----------|
| **Local LLM over API** | Privacy, no vendor lock-in, cost control |
| **Embeddable widget first** | Easier city adoption vs. standalone |
| **Text-only MVP** | Faster to build, covers 90% of use cases |
| **Simple CMS** | Avoid feature bloat; cities will maintain content |