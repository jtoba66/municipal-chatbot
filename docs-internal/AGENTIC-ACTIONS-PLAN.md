# Agentic Actions Implementation Plan

**Project:** Municipal Chatbot  
**Feature:** Agentic Actions (Form Automation)  
**Last Updated:** March 2025

---

## Overview

This plan details the implementation of **Agentic Actions** — allowing citizens to complete municipal tasks (report issues, book permits, pay tickets) directly through the chatbot by automating form submission via Playwright.

**Prerequisites (Completed):**
- ✅ LLM can detect action intents (see `llm-intent-test.md`)
- ✅ City portal fields documented (see `agentic-actions-research.md`)

---

## 1. User Flow

### 1.1 Triggering an Action

```
User Message → Intent Detection (LLM) → Action Classification
```

**How users trigger actions:**
1. **Explicit**: "I want to report a pothole", "Book me a parking permit"
2. **Implicit**: "There's a big hole on King Street" (LLM infers report action)

The LLM classifies the message as either:
- `QUESTION` (answer with RAG)
- `ACTION_REQUEST` (initiate agentic action)

### 1.2 Field Collection (Missing Fields Loop)

```
Collect Fields → Ask User → Validate → Repeat until complete
```

**Field Collection Flow:**
1. LLM extracts available fields from user message
2. System identifies missing required fields (per action schema)
3. Chatbot prompts user for ONE missing field at a time
4. User provides answer
5. Validate format (e.g., license plate format, email format)
6. Repeat until all required fields collected

**Example Conversation:**
```
User: I want to report a pothole on King Street
Bot: I can help you report that pothole. What type of issue is this? (Options: Graffiti, Illegal sign, Litter, Pothole, Sidewalk hazard, Other)
User: Pothole
Bot: Thanks. Now, please provide a description of the pothole (size, damage, etc.):
User: It's about a foot wide and getting bigger
Bot: Got it. Finally, please provide your contact name:
User: John Smith
Bot: Your report is ready to submit:
  - Issue: Pothole
  - Location: King Street
  - Description: It's about a foot wide and getting bigger
  - Contact: John Smith
  
Should I submit this report? (Yes/No)
```

### 1.3 Confirmation Before Submission

```
Review Summary → User Confirmation → Execute Action
```

**Confirmation Requirements:**
1. Display all collected fields in structured format
2. Clearly state what will happen ("I will submit this to the City of Kitchener")
3. Ask explicit yes/no confirmation
4. If "No": Offer to edit specific fields or cancel
5. If "Yes": Proceed to action execution

### 1.4 Post-Submission Experience

```
Execute Action → Display Result → Offer Next Steps
```

**Post-Submission States:**

| Outcome | User Message | Bot Response |
|---------|--------------|--------------|
| **Success** | — | "✅ Report submitted! Your confirmation number is [XYZ]. You should receive an email confirmation within 24 hours." |
| **Partial Success** | — | "⚠️ Report submitted but could not get confirmation number. Please save this reference: [session ID]. Contact 519-741-2345 if you don't receive email within 2 days." |
| **Failure** | — | "❌ Unable to complete your request at this time. The city's form may be temporarily unavailable. Would you like me to open the form in a new tab so you can try yourself?" |
| **Manual Required** | — | "This type of request requires personal attention. Would you like me to prepare an email to 311@kitchener.ca with your information?" |

---

## 2. Required Changes

### 2.1 Backend Changes

| Component | Description | New File |
|-----------|-------------|----------|
| **Intent Detection Middleware** | Intercepts messages, calls LLM to classify as QUESTION or ACTION_REQUEST | `backend/middleware/intentDetector.js` |
| **Action Registry** | Maps action names to handler modules and field schemas | `backend/actions/registry.js` |
| **Field Collection Engine** | Manages state machine for collecting missing fields per action | `backend/actions/fieldCollector.js` |
| **Confirmation Handler** | Generates review summary, handles yes/no responses | `backend/actions/confirmationHandler.js` |
| **Action Base Class** | Abstract class defining execute(), validate(), getFields() | `backend/actions/base.js` |

### 2.2 Frontend Changes

| Component | Description | File |
|-----------|-------------|------|
| **Confirmation Dialog** | Modal showing review summary before submission | `frontend/src/components/ActionConfirmation.tsx` |
| **Action Progress Indicator** | Shows "Collecting: Location → Description → Contact" | `frontend/src/components/ActionProgress.tsx` |
| **Success/Error Cards** | Styled result cards after action submission | `frontend/src/components/ActionResult.tsx` |
| **Field Input Components** | Specialized inputs (address autocomplete, date picker) | `frontend/src/components/ActionInputs.tsx` |

### 2.3 New Files Per Action

Each action gets its own module in `backend/actions/`:

| Action | File | Key Fields |
|--------|------|------------|
| Report Issue | `reportIssue.js` | issue_type, location, description, contact_name, contact_email, contact_phone |
| Book Parking Permit | `bookParkingPermit.js` | parking_location, email, license_plate, phone |
| Check Permit Status | `checkPermitStatus.js` | permit_number OR address |
| Pay Parking Ticket | `payParkingTicket.js` | ticket_number (Kitchener) OR license_plate + ticket_number (Waterloo) |
| Schedule Inspection | `scheduleInspection.js` | permit_number, inspection_type, preferred_date, preferred_time |

### 2.4 Playwright Automation Scripts

Each action needs a Playwright automation script:

```
backend/actions/automation/
├── kitchener/
│   ├── reportIssue.js      # Fills form.kitchener.ca
│   ├── bookParkingPermit.js
│   ├── checkPermitStatus.js
│   ├── payTicket.js
│   └── scheduleInspection.js
└── waterloo/
    ├── reportIssue.js
    ├── bookParkingPermit.js
    └── payTicket.js
```

---

## 3. Priority Order

### Rationale: Start Simplest → Most Complex

| Priority | Action | Reason |
|----------|--------|--------|
| **1** | Pay Parking Ticket | Fewest fields (1-2), payment is external (not our problem), clear success/fail |
| **2** | Report Issue | Simple form, no authentication, good test case for field collection |
| **3** | Book Parking Permit | More fields, but straightforward |
| **4** | Check Permit Status | Read-only (no form submission), just scraping/API |
| **5** | Schedule Inspection | Most complex: requires permit validation, date/time scheduling |

### City Prioritization

| Phase | City | Reason |
|-------|------|--------|
| **Phase 1** | Kitchener | Better documented portals, parking permit site simpler |
| **Phase 2** | Waterloo | Add after Phase 1 is stable |

---

## 4. Technical Implementation Details

### 4.1 Intent Detection Prompt

```javascript
const INTENT_PROMPT = `You are a municipal chatbot intent classifier.
Classify the user's message as either:
- QUESTION: User wants information (garbage day, parking rules, etc.)
- ACTION_REQUEST: User wants to DO something (report issue, book permit, pay ticket)

Also extract:
- action_type: The specific action (report_issue, book_parking_permit, pay_ticket, check_permit, schedule_inspection)
- city: Detected city (kitchener, waterloo, or unknown)
- fields: Any fields already provided by user

Respond in JSON format:
{ "intent": "QUESTION|ACTION_REQUEST", "action_type": "...", "city": "...", "fields": {...} }`;
```

### 4.2 Action Schema Format

```javascript
// Example: Report Issue Schema
const reportIssueSchema = {
  action: 'report_issue',
  city: 'kitchener', // or 'waterloo'
  required_fields: [
    { name: 'issue_type', type: 'select', options: ['Graffiti', 'Pothole', 'Litter', ...] },
    { name: 'location', type: 'text', validation: 'address' },
    { name: 'description', type: 'textarea', maxLength: 500 },
    { name: 'contact_name', type: 'text' },
    { name: 'contact_email', type: 'email' },
    { name: 'contact_phone', type: 'phone' }
  ],
  portal_url: 'https://form.kitchener.ca/CSD/CCS/Report-a-problem',
  automation_script: 'kitchener/reportIssue.js'
};
```

### 4.3 State Machine: Field Collection

```
[IDLE] → User message with action intent → [COLLECTING_FIELDS]
[COLLECTING_FIELDS] → All fields complete → [AWAITING_CONFIRMATION]
[AWAITING_CONFIRMATION] → User says "Yes" → [EXECUTING_ACTION]
[EXECUTING_ACTION] → Success/Fail → [IDLE]
[AWAITING_CONFIRMATION] → User says "No" → [EDITING] → [COLLECTING_FIELDS]
```

---

## 5. Error Handling

### 5.1 Form Automation Failures

| Failure Mode | Handling |
|--------------|----------|
| Portal timeout | Retry 3 times with exponential backoff |
| CAPTCHA detected | Abort and offer manual link |
| Session expired | Abort and offer manual link |
| Invalid field value | Re-prompt with validation error |
| Payment required | Return payment URL (external) |

### 5.2 Fallback Options

For any failure, always offer:
1. "Open form in new tab" — direct link to city portal
2. "Save my information" — store for later / email to user
3. "Contact 311" — provide phone number

---

## 6. Security Considerations

| Concern | Mitigation |
|---------|------------|
| **PII Exposure** | Don't log user data in automation scripts; use ephemeral browser context |
| **Form Abuse** | Rate limit actions per session (max 3 per hour) |
| **Credential Storage** | No stored credentials; all actions as anonymous citizen |
| **Injection** | Sanitize all user input before passing to Playwright |

---

## 7. Metrics & Success Criteria

| Metric | Target |
|--------|--------|
| Action completion rate | ≥70% of started actions complete |
| Field collection abandonment | <20% drop off during collection |
| Automation success rate | ≥85% on first attempt |
| User satisfaction (post-action) | ≥4.0/5.0 |

---

## 8. Out of Scope (v1)

- Payment processing within chatbot (use city payment portal)
- Real-time permit status updates (scrape is acceptable)
- PDF receipt generation
- Multi-step wizard for complex actions
- Action history / undo