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
  setSessionId: (id: string) => void
  setUserInfo: (info: UserInfo) => void
  setInitialized: (initialized: boolean) => void
  addMessage: (message: Message) => void
  setTyping: (typing: boolean) => void
  setConnected: (connected: boolean) => void
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

      setSessionId: (id) => set({ sessionId: id }),

      setUserInfo: (info) => set({ userInfo: info }),

      setInitialized: (initialized) => set({ isInitialized: initialized }),

      addMessage: (message) =>
        set((state) => ({
          messages: [...state.messages, message],
        })),

      setTyping: (typing) => set({ isTyping: typing }),

      setConnected: (connected) => set({ isConnected: connected }),

      resetSession: () =>
        set({
          sessionId: null,
          userInfo: null,
          isInitialized: false,
          messages: [],
          isTyping: false,
          isConnected: false,
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