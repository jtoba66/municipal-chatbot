import { Message, UserInfo } from '../hooks/useChatStore'

// Use environment variable or default to local
// For production, set VITE_API_URL to your backend URL
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Override for testing with public tunnel
const BACKEND_URL = 'https://motion-actual-sensor-factory.trycloudflare.com'
const USE_PUBLIC_URL = true

export interface ChatResponse {
  answer: string  // Backend returns "answer" not "message"
  sources: Array<{ title: string; url: string; content?: string }>
}

export interface SessionResponse {
  session_id: string
  created_at: string
}

export interface HealthStatus {
  status: 'ok' | 'degraded' | 'down'
  ollama: 'connected' | 'disconnected'
  db: 'connected' | 'disconnected'
}

export interface FeedbackRequest {
  session_id: string
  message_id?: number
  rating: number
  feedback_text?: string
}

export interface FeedbackResponse {
  status: string
  feedback_id: number
}

export const api = {
  getBaseUrl() {
    return USE_PUBLIC_URL ? BACKEND_URL : API_BASE
  },

  async checkHealth(): Promise<HealthStatus> {
    const response = await fetch(`${this.getBaseUrl()}/api/health`)
    if (!response.ok) throw new Error('Health check failed')
    return response.json()
  },

  async createSession(userInfo: UserInfo): Promise<SessionResponse> {
    const response = await fetch(`${this.getBaseUrl()}/api/session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userInfo),
    })
    if (!response.ok) throw new Error('Failed to create session')
    return response.json()
  },

  async sendMessage(
    sessionId: string,
    message: string,
    history: Message[]
  ): Promise<ChatResponse> {
    const response = await fetch(`${this.getBaseUrl()}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message,
        history: history.map((m) => ({
          role: m.role,
          content: m.content,
        })),
      }),
    })
    if (!response.ok) throw new Error('Failed to send message')
    return response.json()
  },

  async endSession(sessionId: string): Promise<{ success: boolean }> {
    const response = await fetch(`${this.getBaseUrl()}/api/session/${sessionId}/end`, {
      method: 'POST',
    })
    if (!response.ok) throw new Error('Failed to end session')
    return response.json()
  },

  async getSessionHistory(sessionId: string): Promise<{ messages: Message[] }> {
    const response = await fetch(`${this.getBaseUrl()}/api/session/${sessionId}`)
    if (!response.ok) throw new Error('Failed to get session history')
    return response.json()
  },

  async submitFeedback(feedback: FeedbackRequest): Promise<FeedbackResponse> {
    const response = await fetch(`${this.getBaseUrl()}/api/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(feedback),
    })
    if (!response.ok) throw new Error('Failed to submit feedback')
    return response.json()
  },
}