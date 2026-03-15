interface ChatHeaderProps {
  userName: string
  onEndChat: () => void
}

export function ChatHeader({ userName, onEndChat }: ChatHeaderProps) {
  return (
    <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-kw-blue to-kw-teal text-white shadow-lg">
      <div className="flex items-center gap-3">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
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
              d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
            />
          </svg>
        </div>
        <div>
          <h2 className="font-semibold text-sm">Municipal Chat</h2>
          <p className="text-xs text-white/70">Hi, {userName}!</p>
        </div>
      </div>
      <button
        onClick={onEndChat}
        className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm bg-white/10 hover:bg-white/20 transition-colors"
      >
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
          />
        </svg>
        End Chat
      </button>
    </div>
  )
}