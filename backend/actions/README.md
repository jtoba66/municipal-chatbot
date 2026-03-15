# Agentic Actions Backend

This module provides the backend infrastructure for the Municipal Chatbot's agentic actions feature, enabling automated citizen service actions like paying parking tickets, reporting issues, and booking permits.

## Structure

```
backend/actions/
├── __init__.py           # Module exports
├── base.py               # Base Action class and schemas
├── registry.py           # Action registry with schemas
├── field_collector.py    # Field collection state machine
├── intent_detector.py    # Intent classification middleware
└── automation/
    └── kitchener/
        └── pay_ticket.py  # Playwright automation for paying tickets
```

## API Endpoints

### Intent Classification
- **POST /api/intent/classify** - Classify user message as QUESTION, ACTION_REQUEST, or GREETING

### Actions Management
- **GET /api/actions** - List all available actions
- **GET /api/actions/{action}/schema** - Get field schema for an action
- **POST /api/action/start** - Start a new action flow
- **POST /api/action/collect** - Collect field values from user
- **POST /api/action/confirm** - Confirm/cancel action
- **GET /api/action/status/{session_id}** - Get current action status
- **DELETE /api/action/{session_id}** - Cancel active action

## Available Actions

| Action | City | Description | Required Fields |
|--------|------|-------------|-----------------|
| pay_ticket | Kitchener | Pay parking ticket | ticket_number |
| pay_ticket_waterloo | Waterloo | Pay parking ticket | license_plate, penalty_number |
| report_issue | Kitchener | Report municipal issue | issue_type, location, description, contact_name, contact_email |
| book_parking_permit | Kitchener | Book monthly permit | parking_location, email, license_plate, phone |
| check_permit_status | Kitchener | Check permit status | search_type, search_value |
| schedule_inspection | Kitchener | Schedule inspection | permit_number, inspection_type, preferred_date, preferred_time |

## Usage Example

### Starting an action
```bash
curl -X POST http://localhost:8000/api/action/start \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user123",
    "action": "pay_ticket",
    "city": "kitchener"
  }'
```

Response:
```json
{
  "status": "started",
  "session_id": "user123",
  "action": "pay_ticket",
  "required_fields": ["ticket_number"],
  "missing_fields": ["ticket_number"],
  "prompt": "Please provide: Ticket Number",
  "state": "collecting"
}
```

### Collecting fields
```bash
curl -X POST http://localhost:8000/api/action/collect \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user123",
    "message": "My ticket number is A123456"
  }'
```

### Confirming action
```bash
curl -X POST http://localhost:8000/api/action/confirm \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "user123",
    "confirmed": true
  }'
```

## Key Features

1. **LLM-based Intent Detection** - Uses LLM to classify messages as questions, actions, or greetings
2. **Fallback Classification** - Rule-based fallback when LLM is unavailable
3. **Field Collection State Machine** - Tracks collected/missing fields per session
4. **Batch Field Collection** - Asks for ALL missing fields at once (not one at a time)
5. **Playwright Automation** - Pre-built automation scripts for portal actions

## Testing

Run the test suite:
```bash
cd backend
source .venv/bin/activate
python3 -m pytest tests/
```

Or test endpoints manually with TestClient:
```bash
cd backend
source .venv/bin/activate
python3 -c "
from fastapi.testclient import TestClient
import main

client = TestClient(main.app)
response = client.get('/api/actions')
print(response.json())
"
```