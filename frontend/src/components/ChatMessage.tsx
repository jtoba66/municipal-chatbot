import { useState } from 'react'
import { Message } from '../hooks/useChatStore'
import { api } from '../api/chat'

interface ChatMessageProps {
  message: Message
  sessionId: string
}

export function ChatMessage({ message, sessionId }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const [feedbackGiven, setFeedbackGiven] = useState<number | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleFeedback = async (rating: number) => {
    if (isSubmitting || feedbackGiven) return
    
    setIsSubmitting(true)
    try {
      await api.submitFeedback({
        session_id: sessionId,
        rating,
      })
      setFeedbackGiven(rating)
    } catch (err) {
      console.error('Failed to submit feedback:', err)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} animate-slide-up`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-gradient-to-r from-kw-blue to-kw-teal text-white'
            : 'bg-white text-kw-slate shadow-md border border-gray-100'
        }`}
      >
        <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>

        {/* Source Citations */}
        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-3 pt-3 border-t border-gray-100">
            <p className="text-xs font-medium text-gray-500 mb-2">Sources:</p>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((source, index) => (
                <a
                  key={index}
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="source-link text-xs px-2 py-1 rounded-md bg-kw-blue/5 text-kw-blue hover:bg-kw-blue/10"
                >
                  {source.title}
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Timestamp */}
        <div className="flex items-center justify-between mt-1">
          <p
            className={`text-xs ${
              isUser ? 'text-white/60' : 'text-gray-400'
            }`}
          >
            {message.timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </p>

          {/* Feedback Buttons - Only for assistant messages */}
          {!isUser && (
            <div className="flex items-center gap-1 ml-4">
              <button
                onClick={() => handleFeedback(1)}
                disabled={feedbackGiven !== null}
                className={`p-1 rounded hover:bg-gray-100 transition-colors ${
                  feedbackGiven === 1 ? 'text-green-500' : 'text-gray-400 hover:text-gray-600'
                } ${feedbackGiven ? 'opacity-50' : ''}`}
                title="Not helpful"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                  <path d="M15.73 3H8.27L3 8.27v7.46L8.27 21h7.46L21 15.73V8.27L15.73 3zM12 17.3c-.72 0-1.3-.58-1.3-1.3 0-.72.58-1.3 1.3-1.3.72 0 1.3.58 1.3 1.3 0 .72-.58 1.3-1.3 1.3zm1-4.3h-2V7h2v6z" />
                </svg>
              </button>
              <button
                onClick={() => handleFeedback(5)}
                disabled={feedbackGiven !== null}
                className={`p-1 rounded hover:bg-gray-100 transition-colors ${
                  feedbackGiven === 5 ? 'text-green-500' : 'text-gray-400 hover:text-gray-600'
                } ${feedbackGiven ? 'opacity-50' : ''}`}
                title="Helpful"
              >
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4">
                  <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                </svg>
              </button>
              {feedbackGiven && (
                <span className="text-xs text-green-500 ml-1">Thanks!</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}