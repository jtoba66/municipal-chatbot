type ActionResultStatus = 'loading' | 'success' | 'error' | 'partial'

interface ActionResultProps {
  status: ActionResultStatus
  actionLabel: string
  message?: string
  confirmationNumber?: string
  onRetry?: () => void
  onOpenForm?: () => void
  onContact311?: () => void
}

export function ActionResult({
  status,
  actionLabel,
  message,
  confirmationNumber,
  onRetry,
  onOpenForm,
  onContact311,
}: ActionResultProps) {
  if (status === 'loading') {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-gray-100 p-6">
        <div className="flex flex-col items-center text-center">
          <div className="w-12 h-12 mb-4">
            <svg className="animate-spin h-12 w-12 text-kw-blue" viewBox="0 0 24 24">
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
          </div>
          <h3 className="text-lg font-semibold text-gray-800 mb-2">
            Submitting Your Request
          </h3>
          <p className="text-gray-500">
            Please wait while we submit your {actionLabel.toLowerCase()} to the city...
          </p>
        </div>
      </div>
    )
  }

  if (status === 'success') {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-green-100 overflow-hidden">
        <div className="bg-green-50 px-4 py-3 border-b border-green-100">
          <div className="flex items-center gap-2 text-green-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <span className="font-semibold">Request Submitted Successfully!</span>
          </div>
        </div>

        <div className="p-4">
          <p className="text-gray-700 mb-4">
            ✅ Your <strong>{actionLabel.toLowerCase()}</strong> has been submitted. You should
            receive a confirmation email within 24 hours.
          </p>

          {confirmationNumber && (
            <div className="bg-green-50 rounded-lg p-3 mb-4">
              <span className="text-sm text-green-600 font-medium">Confirmation Number:</span>
              <span className="ml-2 font-mono text-green-800">{confirmationNumber}</span>
            </div>
          )}

          {message && (
            <p className="text-sm text-gray-500 mb-4">{message}</p>
          )}

          <div className="text-sm text-gray-500">
            <p>Thank you for using our municipal services!</p>
          </div>
        </div>
      </div>
    )
  }

  if (status === 'partial') {
    return (
      <div className="bg-white rounded-xl shadow-lg border border-amber-100 overflow-hidden">
        <div className="bg-amber-50 px-4 py-3 border-b border-amber-100">
          <div className="flex items-center gap-2 text-amber-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <span className="font-semibold">Request Submitted (Partial)</span>
          </div>
        </div>

        <div className="p-4">
          <p className="text-gray-700 mb-4">
            ⚠️ Your request was submitted but we couldn't retrieve a confirmation number.
          </p>

          <div className="bg-amber-50 rounded-lg p-3 mb-4">
            <p className="text-sm text-amber-700">
              Please save this reference: <strong>{confirmationNumber || 'Session ID'}</strong>
            </p>
            <p className="text-sm text-amber-600 mt-1">
              Contact 519-741-2345 if you don't receive an email confirmation within 2 days.
            </p>
          </div>

          {message && <p className="text-sm text-gray-500 mb-4">{message}</p>}
        </div>
      </div>
    )
  }

  // Error state
  return (
    <div className="bg-white rounded-xl shadow-lg border border-red-100 overflow-hidden">
      <div className="bg-red-50 px-4 py-3 border-b border-red-100">
        <div className="flex items-center gap-2 text-red-700">
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <span className="font-semibold">Unable to Complete Request</span>
        </div>
      </div>

      <div className="p-4">
        <p className="text-gray-700 mb-4">
          ❌ We're sorry, but we couldn't complete your {actionLabel.toLowerCase()} at this
          time. The city's form may be temporarily unavailable.
        </p>

        {message && (
          <p className="text-sm text-gray-500 mb-4">Error: {message}</p>
        )}

        <div className="space-y-2">
          {onOpenForm && (
            <button
              onClick={onOpenForm}
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-medium
                         hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                />
              </svg>
              Open Form in New Tab
            </button>
          )}

          {onRetry && (
            <button
              onClick={onRetry}
              className="w-full px-4 py-2.5 rounded-lg bg-kw-blue text-white font-medium
                         hover:bg-blue-700 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Try Again
            </button>
          )}

          {onContact311 && (
            <button
              onClick={onContact311}
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-medium
                         hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                />
              </svg>
              Contact 311
            </button>
          )}
        </div>
      </div>
    </div>
  )
}