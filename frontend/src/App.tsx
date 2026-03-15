import { useEffect, useState } from 'react'
import { useChatStore, Message, UserInfo } from './hooks/useChatStore'
import { api } from './api/chat'
import { WelcomeScreen } from './components/WelcomeScreen'
import { ChatWindow } from './components/ChatWindow'

function App() {
  const {
    sessionId,
    userInfo,
    isInitialized,
    messages,
    isTyping,
    setSessionId,
    setUserInfo,
    setInitialized,
    addMessage,
    setTyping,
    resetSession,
  } = useChatStore()

  const [isLoading, setIsLoading] = useState(false)

  // Check if we have a stored session
  useEffect(() => {
    if (sessionId && userInfo) {
      setInitialized(true)
    }
  }, [sessionId, userInfo, setInitialized])

  const handleStartChat = async (info: UserInfo) => {
    setIsLoading(true)

    try {
      // Create session with backend
      const response = await api.createSession(info)
      setSessionId(response.session_id)
      setUserInfo(info)
      setInitialized(true)
    } catch (err) {
      console.error('Failed to create session:', err)
      // For demo purposes, continue even if backend is unavailable
      setSessionId(`demo_${Date.now()}`)
      setUserInfo(info)
      setInitialized(true)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async (content: string) => {
    if (!sessionId || isTyping) return

    // Add user message
    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date(),
    }
    addMessage(userMessage)

    // Show typing indicator
    setTyping(true)

    try {
      const response = await api.sendMessage(sessionId, content, messages)

      // Add assistant response
      const assistantMessage: Message = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        timestamp: new Date(),
      }
      addMessage(assistantMessage)
    } catch (err) {
      console.error('Failed to send message:', err)

      // Demo response when backend is unavailable
      const demoResponses: Record<string, string> = {
        default:
          "I'd be happy to help you with that! For more specific information, please visit the City of Kitchener or City of Waterloo website, or call 311.",
        garbage:
          'Garbage collection in Kitchener/Waterloo varies by zone. Generally, garbage is collected weekly on your scheduled day. Blue box recycling is bi-weekly. Visit your city website to check your schedule.',
        parking:
          'Parking regulations vary by zone. Street parking typically has a 3-hour limit. Paid parking is available in downtown areas. Visit your city website for rates and permit information.',
        permits:
          'Building permits, event permits, and other permits can be applied for through your city website or in person at City Hall. Processing times vary by permit type.',
        taxes:
          'Property tax bills are mailed annually in January. You can pay online, by phone, or in person. Interim tax bills are issued throughout the year.',
      }

      const lowerContent = content.toLowerCase()
      let responseContent = demoResponses.default

      for (const [key, value] of Object.entries(demoResponses)) {
        if (lowerContent.includes(key) && key !== 'default') {
          responseContent = value
          break
        }
      }

      const assistantMessage: Message = {
        id: `msg_${Date.now()}_assistant`,
        role: 'assistant',
        content: responseContent,
        sources: [
          { title: 'City of Kitchener', url: 'https://www.kitchener.ca' },
          { title: 'City of Waterloo', url: 'https://www.waterloo.ca' },
        ],
        timestamp: new Date(),
      }
      addMessage(assistantMessage)
    } finally {
      setTyping(false)
    }
  }

  const handleEndChat = async () => {
    if (sessionId) {
      try {
        await api.endSession(sessionId)
      } catch (err) {
        console.error('Failed to end session:', err)
      }
    }
    resetSession()
  }

  // Show welcome screen if not initialized
  if (!isInitialized) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <WelcomeScreen onSubmit={handleStartChat} isLoading={isLoading} />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      {/* Chat Widget Container */}
      <div className="w-full max-w-lg h-[600px] rounded-2xl shadow-2xl overflow-hidden bg-white">
        <ChatWindow onEndChat={handleEndChat} onSendMessage={handleSendMessage} />
      </div>
    </div>
  )
}

export default App