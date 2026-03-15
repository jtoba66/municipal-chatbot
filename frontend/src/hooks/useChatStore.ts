import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: Date
}

export interface Source {
  title: string
  url: string
}

export interface UserInfo {
  name: string
  email: string
}

// Action-related types
export type ActionStatus = 'idle' | 'collecting' | 'confirming' | 'executing' | 'success' | 'error' | 'partial'

export interface ActionData {
  actionType: string
  actionLabel: string
  city: string
  fields: Record<string, string>
  portalUrl?: string
}

interface ChatState {
  // Session
  sessionId: string | null
  userInfo: UserInfo | null
  isInitialized: boolean

  // Chat
  messages: Message[]
  isTyping: boolean
  isConnected: boolean

  // Actions
  actionStatus: ActionStatus
  currentAction: ActionData | null
  confirmationNumber: string | null
  actionError: string | null

  // Action methods
  setSessionId: (id: string) => void
  setUserInfo: (info: UserInfo) => void
  setInitialized: (initialized: boolean) => void
  addMessage: (message: Message) => void
  setTyping: (typing: boolean) => void
  setConnected: (connected: boolean) => void
  setActionStatus: (status: ActionStatus) => void
  setCurrentAction: (action: ActionData | null) => void
  setConfirmationNumber: (num: string | null) => void
  setActionError: (error: string | null) => void
  resetSession: () => void
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      sessionId: null,
      userInfo: null,
      isInitialized: false,
      messages: [],
      isTyping: false,
      isConnected: false,

      // Action state
      actionStatus: 'idle',
      currentAction: null,
      confirmationNumber: null,
      actionError: null,

      setSessionId: (id) => set({ sessionId: id }),

      setUserInfo: (info) => set({ userInfo: info }),

      setInitialized: (initialized) => set({ isInitialized: initialized }),

      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),

      setTyping: (typing) => set({ isTyping: typing }),

      setConnected: (connected) => set({ isConnected: connected }),

      setActionStatus: (status) => set({ actionStatus: status }),

      setCurrentAction: (action) => set({ currentAction: action }),

      setConfirmationNumber: (num) => set({ confirmationNumber: num }),

      setActionError: (error) => set({ actionError: error }),

      resetSession: () =>
        set({
          sessionId: null,
          userInfo: null,
          isInitialized: false,
          messages: [],
          isTyping: false,
          isConnected: false,
          actionStatus: 'idle',
          currentAction: null,
          confirmationNumber: null,
          actionError: null,
        }),
    }),
    {
      name: 'municipal-chat-storage',
      partialize: (state) => ({
        sessionId: state.sessionId,
        userInfo: state.userInfo,
      }),
    }
  )
)