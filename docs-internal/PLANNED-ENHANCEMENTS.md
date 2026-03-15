## Phase 2 & 3 Planned Enhancements

### 1. Image Upload (Problem Reporting)
- User takes photo of pothole, graffiti, broken streetlight
- Vision model (local LLaVA or CLIP) identifies issue
- Auto-fills service request form
- Submits to city 311 system

### 2. Translation (Text)
- Use argos translate or LibreTranslate (self-hosted)
- French required for Ontario services
- Auto-translate incoming/outgoing messages
- Cost: near zero, CPU-based

### 3. Memory Across Sessions
- Link sessions by email
- Remember past questions
- "Based on our last conversation about your permit..."
- Build citizen profile over time in SQLite

### 4. Agentic Actions
- Report pothole → submits to 311 API
- Book parking permit → fills form, submits
- Check permit status → scrapes or API call
- Pay ticket → links to payment portal
- Schedule inspection → books slot

### 5. Knowledge Graph
- Hybrid: RAG for simple Q&A, KG for complex queries
- Connect entities: dates, locations, people
- Answer multi-hop questions
- Use NetworkX + vector hybrid