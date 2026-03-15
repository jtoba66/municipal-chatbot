import { useState } from 'react'
import { UserInfo } from '../hooks/useChatStore'

interface WelcomeScreenProps {
  onSubmit: (userInfo: UserInfo) => void
  isLoading?: boolean
}

export function WelcomeScreen({ onSubmit, isLoading }: WelcomeScreenProps) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) {
      setError('Please enter your name')
      return
    }
    setError('')
    onSubmit({ name: name.trim(), email: email.trim() })
  }

  return (
    <div className="flex flex-col items-center justify-center h-full p-6 bg-gradient-to-br from-kw-blue/5 to-kw-teal/5">
      <div className="w-full max-w-md">
        {/* Logo / Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 mb-4 rounded-2xl bg-gradient-to-br from-kw-blue to-kw-teal shadow-lg">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-kw-slate mb-2">
            Welcome to Municipal Chat
          </h1>
          <p className="text-civic-stone/70">
            Get instant answers about local services, programs, and more
          </p>
        </div>

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="glass rounded-2xl p-6 shadow-xl"
        >
          <div className="space-y-4">
            <div>
              <label
                htmlFor="name"
                className="block text-sm font-medium text-kw-slate mb-1"
              >
                Your Name <span className="text-red-500">*</span>
              </label>
              <input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Enter your name"
                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-kw-blue focus:ring-2 focus:ring-kw-blue/20 outline-none transition-all"
                disabled={isLoading}
              />
            </div>

            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-kw-slate mb-1"
              >
                Email <span className="text-gray-400">(optional)</span>
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Receive a summary of your chat"
                className="w-full px-4 py-3 rounded-xl border border-gray-200 focus:border-kw-blue focus:ring-2 focus:ring-kw-blue/20 outline-none transition-all"
                disabled={isLoading}
              />
              <p className="mt-1 text-xs text-gray-500">
                We'll send you a summary and remember your address for future visits
              </p>
            </div>

            {error && (
              <p className="text-sm text-red-500">{error}</p>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-6 rounded-xl bg-gradient-to-r from-kw-blue to-kw-teal text-white font-semibold shadow-lg shadow-kw-blue/25 hover:shadow-xl hover:shadow-kw-blue/30 transform hover:-translate-y-0.5 transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                      fill="none"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Starting chat...
                </span>
              ) : (
                'Start Chat'
              )}
            </button>
          </div>
        </form>

        {/* Info */}
        <p className="mt-6 text-center text-xs text-gray-400">
          By starting a chat, you agree to our{' '}
          <a href="#" className="text-kw-blue hover:underline">
            Privacy Policy
          </a>
        </p>
      </div>
    </div>
  )
}