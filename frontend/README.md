# Municipal Chatbot - Frontend

React frontend for the Kitchener/Waterloo Municipal Chatbot.

## Features

- ✅ Welcome Screen - Captures user name and email before chat
- ✅ Chat Interface - Messages display, input field, send button
- ✅ Typing Indicator - Shows when AI is thinking
- ✅ Source Citations - Shows source links for responses
- ✅ End Chat Button - Ends session and triggers email summary
- ✅ Responsive Design - Works on mobile and desktop
- ✅ Accessible - WCAG compliant

## Tech Stack

- React 18 + TypeScript
- Tailwind CSS
- Zustand (state management)
- Vite (build tool)

## Getting Started

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## API Configuration

Set the API base URL via environment variable:

```bash
VITE_API_URL=http://localhost:8000 npm run dev
```

## Backend API Endpoints

- `POST /api/session` - Create new session with user info
- `GET /api/session/{id}` - Get session history
- `POST /api/chat` - Send message, get AI response
- `POST /api/session/{id}/end` - End session and send email summary
- `GET /api/health` - Health check