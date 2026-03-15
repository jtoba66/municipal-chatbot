import { useState, useRef, useEffect } from 'react'

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
}

export function ChatInput({ onSend, disabled, placeholder }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`
    }
  }, [message])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = message.trim()
    if (!trimmed || disabled) return

    onSend(trimmed)
    setMessage('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex items-end gap-2 p-4 bg-white border-t border-gray-100"
    >
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder || 'Type your message...'}
          disabled={disabled}
          rows={1}
          className="w-full px-4 py-3 pr-12 rounded-xl border border-gray-200 focus:border-kw-blue focus:ring-2 focus:ring-kw-blue/20 outline-none resize-none transition-all disabled:bg-gray-50 disabled:cursor-not-allowed"
        />
      </div>
      <button
        type="submit"
        disabled={disabled || !message.trim()}
        className="flex-shrink-0 w-12 h-12 flex items-center justify-center rounded-xl bg-gradient-to-r from-kw-blue to-kw-teal text-white shadow-lg shadow-kw-blue/25 hover:shadow-xl hover:shadow-kw-blue/30 transform hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
      >
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
          />
        </svg>
      </button>
    </form>
  )
}