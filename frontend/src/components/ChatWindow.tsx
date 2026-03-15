import { useRef, useEffect } from 'react'
import { useChatStore } from '../hooks/useChatStore'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { ChatHeader } from './ChatHeader'
import { TypingIndicator } from './TypingIndicator'

interface ChatWindowProps {
  onEndChat: () => void
  onSendMessage: (message: string) => void
}

export function ChatWindow({ onEndChat, onSendMessage }: ChatWindowProps) {
  const { messages, isTyping, userInfo, sessionId } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping])

  return (
    <div className="flex flex-col h-full bg-gradient-to-b from-gray-50 to-white">
      <ChatHeader userName={userInfo?.name || 'User'} onEndChat={onEndChat} />

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
        {/* Welcome message */}
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="inline-flex items-center justify-center w-12 h-12 mb-3 rounded-full bg-kw-blue/10">
              <svg
                className="w-6 h-6 text-kw-blue"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </div>
            <p className="text-kw-slate font-medium">
              How can we help you today?
            </p>
            <p className="text-sm text-gray-500 mt-1">
              Ask about garbage collection, parking, permits, services, and
              more!
            </p>
          </div>
        )}

        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} sessionId={sessionId || ''} />
        ))}

        {isTyping && <TypingIndicator />}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSend={onSendMessage}
        disabled={isTyping}
        placeholder="Ask about municipal services..."
      />
    </div>
  )
}