export function TypingIndicator() {
  return (
    <div className="flex justify-start animate-fade-in">
      <div className="bg-white rounded-2xl px-4 py-3 shadow-md border border-gray-100">
        <div className="flex items-center gap-1">
          <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full" />
          <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full" />
          <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full" />
        </div>
      </div>
    </div>
  )
}