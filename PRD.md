# Municipal Chatbot - Product Requirements Document

**Project:** Municipal Chatbot for Kitchener/Waterloo Region  
**Version:** 1.0  
**Status:** Draft for Engineering  
**PM:** Jared (Product Manager)

---

## 1. Problem Statement

Citizens of Kitchener, Waterloo, and the broader Waterloo Region need quick, accurate answers to municipal service questions. Current channels are inadequate:

- **311 phone lines** are overloaded with repetitive questions (garbage schedules, parking, permits, taxes)
- **City websites** have poor UX; citizens can't find information quickly
- **March 2026 cart-based waste rollout** has created confusion for 161,000+ households with no adequate support channel
- **Existing solutions** (municiPal AI pilot) may not meet full needs; cities want vendor options

**Core Problem:** Citizens can't get instant answers to common municipal questions, leading to frustrated residents and overloaded city staff.

---

## 2. Target Users

### Primary Users (Citizens)
- **Resident seeking service info**: "When is my garbage collected?" "How do I pay a parking ticket?"
- **New resident**: Learning about city services, taxes, by-laws
- **Property owner**: Permit applications, tax inquiries, bylaw questions

### Secondary Users (City Staff)
- **311 Customer Service Reps**: Use chatbot to quickly find answers for callers
- **Communications Team**: Monitor citizen queries to improve public info
- **IT/Operations**: Manage chatbot, review analytics, update content

---

## 3. Core Features

### 3.1 Public-Facing Chatbot
- **Conversational interface**: Natural language Q&A for municipal questions
- **Knowledge domains**: Garbage/recycling, parking, permits, taxes, by-laws, city services
- **Multi-channel**: Embeddable widget for city websites + standalone web page
- **Multilingual support**: English (MVP), French (Phase 2)
- **Hand-off to human**: Escalation path for complex queries to 311

### 3.2 Admin Dashboard
- **Conversation analytics**: Volume, topics, satisfaction ratings
- **Content management**: Update Q&A knowledge base without code
- **User feedback review**: Flag inaccurate responses for review

### 3.3 Technical Requirements
- **Self-hosted backend**: No external API dependencies where possible
- **Local LLM inference**: Ollama for privacy/cost control
- **Open source stack**: Minimize licensing costs
- **RAG pipeline**: Ingest city website content + Open Data Portal

---

## 4. User Stories

### Epic 1: Citizen Q&A Experience
**Story 1.1**: As a resident, I want to ask questions in plain English so I can get answers without searching website menus.  
**Priority**: P0 | **Effort**: M | **Dependencies**: LLM integration, RAG pipeline

**Acceptance Criteria**:
- Given a user asks "When is garbage day for my address?"
- When the chatbot processes the query
- Then it returns the correct collection schedule for that address

---

**Story 1.2**: As a resident, I want the chatbot to work on my phone so I can get answers while away from my computer.  
**Priority**: P0 | **Effort**: S | **Dependencies**: Responsive widget design

**Acceptance Criteria**:
- Given a user accesses the chatbot on a mobile device
- When the chat interface loads
- Then it is fully usable with touch, readable text, and no horizontal scrolling

---

**Story 1.3**: As a resident, I want to see sources for the chatbot's answers so I can verify the information.  
**Priority**: P1 | **Effort**: S | **Dependencies**: RAG pipeline with source tracking

**Acceptance Criteria**:
- Given the chatbot provides an answer
- When the response includes a citation
- Then the user can click the source link to view the original city webpage

---

### Epic 2: Admin Dashboard
**Story 2.1**: As a city communications staff, I want to see what questions citizens are asking most so I can improve public information.  
**Priority**: P1 | **Effort**: M | **Dependencies**: Conversation logging, analytics DB

**Acceptance Criteria**:
- Given the admin logs into the dashboard
- When viewing the analytics page
- Then they see top 20 query topics with frequency counts

---

**Story 2.2**: As an IT admin, I want to update Q&A content without coding so non-technical staff can maintain the chatbot.  
**Priority**: P1 | **Effort**: M | **Dependencies**: Content management API

**Acceptance Criteria**:
- Given an admin accesses the content editor
- When they add a new Q&A pair
- Then it is immediately available to chatbot users

---

### Epic 3: Technical Infrastructure
**Story 3.1**: As the technical lead, I want the system to run locally/offline so we don't depend on external APIs for privacy and cost.  
**Priority**: P0 | **Effort**: L | **Dependencies**: Ollama setup, local model selection

**Acceptance Criteria**:
- Given the server has no internet connection
- When a user submits a query
- Then the chatbot still responds using local LLM inference

---

## 5. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Task Completion Rate** | ≥80% | % of queries resolved without human handoff |
| **Response Time** | <3 seconds | Average response latency |
| **User Satisfaction** | ≥4.0/5.0 | Post-conversation rating |
| **Monthly Active Users** | 5,000 (Y1) | Unique users per month |
| **Cost per Conversation** | <$0.05 | Infrastructure cost / conversation |

---

## 6. Out of Scope (MVP)

- Voice interaction (phonebot)
- Multi-city federation
- AI agent actions (e.g., paying tickets through chat)
- Advanced sentiment analysis
- Integration with 311 ticketing system

---

## 7. Risks & Assumptions

| Risk | Mitigation |
|------|------------|
| **LLM accuracy**: May provide incorrect municipal info | Human review loop, source citations |
| **Privacy**: Citizen data in conversations | Local processing, no external logging |
| **Adoption**: Cities slow to procure | Target existing municiPal customers as replacements |
| **Maintenance**: Content updates require effort | Build easy CMS for city staff |

---

## 8. Technical Constraints (from Architect input expected)

- Self-hosted backend (Docker)
- Ollama for local inference (llama3.2 or smaller model)
- React frontend with chat UI library
- PostgreSQL or SQLite for conversation storage
- RAG using LangChain or similar