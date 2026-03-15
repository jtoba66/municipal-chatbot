import { useState } from 'react'

export interface ActionData {
  actionType: string
  actionLabel: string
  city: string
  fields: Record<string, string>
}

interface ConfirmationDialogProps {
  action: ActionData
  onConfirm: () => void
  onCancel: () => void
  onEditField?: (fieldName: string) => void
}

export function ConfirmationDialog({
  action,
  onConfirm,
  onCancel,
  onEditField,
}: ConfirmationDialogProps) {
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleConfirm = async () => {
    setIsSubmitting(true)
    try {
      await onConfirm()
    } finally {
      setIsSubmitting(false)
    }
  }

  // Format field name for display
  const formatFieldName = (key: string): string => {
    return key
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ')
  }

  // Get action-specific icon
  const getActionIcon = () => {
    switch (action.actionType) {
      case 'report_issue':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        )
      case 'book_parking_permit':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
          </svg>
        )
      case 'pay_ticket':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        )
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        )
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-kw-blue to-blue-600 px-4 py-3">
        <div className="flex items-center gap-2 text-white">
          {getActionIcon()}
          <span className="font-semibold">Confirm Your Request</span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <p className="text-gray-700 mb-4">
          You're about to <strong>{action.actionLabel.toLowerCase()}</strong> for the{' '}
          <strong className="text-kw-blue">{action.city}</strong> area. Please review the
          details below:
        </p>

        {/* Fields Summary */}
        <div className="bg-gray-50 rounded-lg p-3 mb-4 space-y-2">
          {Object.entries(action.fields).map(([key, value]) => (
            <div key={key} className="flex justify-between items-start">
              <span className="text-sm text-gray-500">{formatFieldName(key)}:</span>
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-gray-800 text-right max-w-[180px] break-words">
                  {value || '—'}
                </span>
                {onEditField && (
                  <button
                    onClick={() => onEditField(key)}
                    className="text-xs text-kw-blue hover:text-blue-700 underline"
                  >
                    Edit
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>

        <p className="text-sm text-gray-500 mb-4">
          Once confirmed, this will be submitted to the City of{' '}
          {action.city.charAt(0).toUpperCase() + action.city.slice(1)}.
        </p>
      </div>

      {/* Actions */}
      <div className="flex gap-3 px-4 pb-4">
        <button
          onClick={onCancel}
          disabled={isSubmitting}
          className="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 text-gray-700 font-medium
                     hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Cancel
        </button>
        <button
          onClick={handleConfirm}
          disabled={isSubmitting}
          className="flex-1 px-4 py-2.5 rounded-lg bg-kw-blue text-white font-medium
                     hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed
                     flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
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
              Submitting...
            </>
          ) : (
            <>
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              Confirm & Submit
            </>
          )}
        </button>
      </div>
    </div>
  )
}