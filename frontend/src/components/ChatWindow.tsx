import { useRef, useEffect, useState } from 'react'
import { useChatStore } from '../hooks/useChatStore'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { ChatHeader } from './ChatHeader'
import { TypingIndicator } from './TypingIndicator'
import { ConfirmationDialog, ActionData } from './ConfirmationDialog'
import { ActionResult } from './ActionResult'

interface ChatWindowProps {
  onEndChat: () => void
  onSendMessage: (message: string) => void
}

export function ChatWindow({ onEndChat, onSendMessage }: ChatWindowProps) {
  const { messages, isTyping, userInfo, sessionId, actionStatus, currentAction, confirmationNumber, actionError, setActionStatus, setConfirmationNumber, setActionError } = useChatStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Demo: Store for simulating action flow (would come from backend in production)
  const [demoAction, setDemoAction] = useState<ActionData | null>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isTyping, actionStatus])

  // Handle confirmation
  const handleConfirm = async () => {
    if (!currentAction) return

    setActionStatus('executing')

    // Simulate API call to backend
    setTimeout(() => {
      // Demo: Random success/error for testing
      const isSuccess = Math.random() > 0.2
      if (isSuccess) {
        setConfirmationNumber(`CFM-${Date.now().toString(36).toUpperCase()}`)
        setActionStatus('success')
      } else {
        setActionError('City portal temporarily unavailable')
        setActionStatus('error')
      }
    }, 2000)
  }

  // Handle cancel
  const handleCancel = () => {
    setDemoAction(null)
    setActionStatus('idle')
  }

  // Handle retry
  const handleRetry = () => {
    setActionError(null)
    handleConfirm()
  }

  // Handle open form
  const handleOpenForm = () => {
    if (currentAction?.portalUrl) {
      window.open(currentAction.portalUrl, '_blank')
    }
  }

  // Handle contact 311
  const handleContact311 = () => {
    window.location.href = 'tel:5197412345'
  }

  // Show confirmation dialog when action is ready
  if (actionStatus === 'confirming' && currentAction) {
    return (
      <div className="flex flex-col h-full bg-gradient-to-b from-gray-50 to-white">
        <ChatHeader userName={userInfo?.name || 'User'} onEndChat={onEndChat} />
        
        <div className="flex-1 p-4 flex items-center justify-center">
          <ConfirmationDialog
            action={currentAction}
            onConfirm={handleConfirm}
            onCancel={handleCancel}
          />
        </div>
      </div>
    )
  }

  // Show result when action completes
  if ((actionStatus === 'success' || actionStatus === 'error' || actionStatus === 'partial' || actionStatus === 'executing') && currentAction) {
    // Map executing to loading for ActionResult
    const resultStatus = actionStatus === 'executing' ? 'loading' : actionStatus
    return (
      <div className="flex flex-col h-full bg-gradient-to-b from-gray-50 to-white">
        <ChatHeader userName={userInfo?.name || 'User'} onEndChat={onEndChat} />
        
        <div className="flex-1 p-4 flex items-center justify-center">
          <ActionResult
            status={resultStatus}
            actionLabel={currentAction.actionLabel}
            message={actionError || undefined}
            confirmationNumber={confirmationNumber || undefined}
            onRetry={actionStatus === 'error' ? handleRetry : undefined}
            onOpenForm={actionStatus === 'error' ? handleOpenForm : undefined}
            onContact311={actionStatus === 'error' ? handleContact311 : undefined}
          />
        </div>

        {/* Allow starting a new conversation after action completes */}
        {(actionStatus === 'success' || actionStatus === 'partial' || actionStatus === 'error') && (
          <div className="p-4 border-t">
            <button
              onClick={() => {
                setActionStatus('idle')
                setConfirmationNumber(null)
                setActionError(null)
              }}
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-medium
                         hover:bg-gray-50 transition-colors"
            >
              Start New Request
            </button>
          </div>
        )}
      </div>
    )
  }

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