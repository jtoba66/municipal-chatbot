/**
 * Municipal Chat Widget
 * Embeddable chat widget for Kitchener/Waterloo municipal services
 * 
 * Usage:
 * <script src="municipal-chat.js" data-api-url="http://localhost:8000"><\/script>
 */
(function() {
  'use strict';
  
  const API_BASE = window['municipalChatApiUrl'] || 'http://localhost:8000';
  const DEFAULT_POSITION = 'bottom-right';
  
  // Demo responses for offline mode
  const DEMO_RESPONSES = {
    default: "I'd be happy to help with that! For more specific information, please visit the City of Kitchener or City of Waterloo website, or call 311.",
    garbage: 'Garbage collection in Kitchener/Waterloo varies by zone. Generally, garbage is collected weekly. Blue box recycling is bi-weekly. Check your city website for your schedule.',
    parking: 'Parking regulations vary by zone. Street parking typically has a 3-hour limit. Paid parking is available downtown. Check your city website for rates.',
    permits: 'Building permits and other permits can be applied for through your city website or at City Hall. Processing times vary by type.',
    taxes: 'Property tax bills are mailed annually in January. You can pay online, by phone, or in person.',
    '311': 'Dial 311 for non-emergency city services, including waste collection, road maintenance, and general inquiries.'
  };
  
  // Widget state
  let state = {
    isOpen: false,
    isInitialized: false,
    sessionId: null,
    userInfo: null,
    messages: [],
    isTyping: false
  };
  
  // Load state from localStorage
  try {
    const savedState = localStorage.getItem('municipal-chat-storage');
    if (savedState) {
      const parsed = JSON.parse(savedState);
      if (parsed.state && parsed.state.sessionId && parsed.state.userInfo) {
        state.sessionId = parsed.state.sessionId;
        state.userInfo = parsed.state.userInfo;
        state.isInitialized = true;
      }
    }
  } catch (e) {}
  
  // Create widget container
  const widget = document.createElement('div');
  widget.id = 'municipal-chat-widget';
  widget.innerHTML = `
    <style>
      #municipal-chat-widget {
        position: fixed;
        bottom: 24px;
        right: 24px;
        z-index: 999999;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
      }
      #municipal-chat-widget * { margin: 0; padding: 0; box-sizing: border-box; }
      
      .mcw-toggle {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: linear-gradient(135deg, #0076A8 0%, #009DAE 100%);
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(0, 118, 168, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: transform 0.2s, box-shadow 0.2s;
      }
      .mcw-toggle:hover { transform: scale(1.05); }
      .mcw-toggle svg { width: 28px; height: 28px; color: white; }
      .mcw-toggle-close { display: none; }
      
      .mcw-container {
        position: absolute;
        bottom: 76px;
        right: 0;
        width: 380px;
        height: 520px;
        max-height: calc(100vh - 100px);
        max-width: calc(100vw - 48px);
        min-width: 320px;
        background: white;
        border-radius: 16px;
        box-shadow: 0 8px 40px rgba(0, 0, 0, 0.15);
        overflow: hidden;
        display: none;
        flex-direction: column;
        animation: mcwSlideUp 0.3s ease-out;
      }
      .mcw-container.open { display: flex; }
      @keyframes mcwSlideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
      }
      
      .mcw-header {
        padding: 16px 20px;
        background: linear-gradient(135deg, #0076A8 0%, #009DAE 100%);
        color: white;
        display: flex;
        align-items: center;
        justify-content: space-between;
      }
      .mcw-header-title { font-weight: 600; font-size: 16px; }
      .mcw-header-subtitle { font-size: 12px; opacity: 0.8; }
      
      .mcw-close-btn, .mcw-end-btn {
        background: rgba(255,255,255,0.2);
        border: none;
        color: white;
        padding: 6px 12px;
        border-radius: 6px;
        cursor: pointer;
        font-size: 12px;
        transition: background 0.2s;
      }
      .mcw-close-btn { width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center; }
      .mcw-end-btn:hover, .mcw-close-btn:hover { background: rgba(255,255,255,0.3); }
      
      .mcw-body {
        flex: 1;
        overflow-y: auto;
        padding: 16px;
        background: linear-gradient(180deg, #f8fafc 0%, #fff 100%);
      }
      
      .mcw-welcome { text-align: center; padding: 32px 16px; }
      .mcw-welcome-icon {
        width: 48px; height: 48px;
        margin: 0 auto 16px;
        background: rgba(0, 118, 168, 0.1);
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
      }
      .mcw-welcome-icon svg { width: 24px; height: 24px; color: #0076A8; }
      .mcw-welcome h3 { color: #2D3748; font-size: 18px; margin-bottom: 8px; }
      .mcw-welcome p { color: #718096; font-size: 14px; }
      
      .mcw-form {
        padding: 20px;
        background: rgba(255,255,255,0.8);
        backdrop-filter: blur(10px);
        border-radius: 12px;
        margin-top: 16px;
      }
      .mcw-form-group { margin-bottom: 16px; }
      .mcw-form-group label { display: block; font-size: 13px; font-weight: 500; color: #2D3748; margin-bottom: 6px; }
      .mcw-form-group label span { color: #a0aec0; font-weight: 400; }
      .mcw-form-group input {
        width: 100%; padding: 12px 14px;
        border: 1px solid #e2e8f0; border-radius: 10px;
        font-size: 14px; outline: none;
        transition: border-color 0.2s, box-shadow 0.2s;
      }
      .mcw-form-group input:focus { border-color: #0076A8; box-shadow: 0 0 0 3px rgba(0, 118, 168, 0.1); }
      
      .mcw-form-btn {
        width: 100%; padding: 12px;
        background: linear-gradient(135deg, #0076A8 0%, #009DAE 100%);
        color: white; border: none; border-radius: 10px;
        font-size: 14px; font-weight: 600;
        cursor: pointer;
        transition: transform 0.2s, box-shadow 0.2s;
      }
      .mcw-form-btn:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0, 118, 168, 0.3); }
      .mcw-form-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
      
      .mcw-messages { display: flex; flex-direction: column; gap: 12px; }
      
      .mcw-message {
        max-width: 85%; padding: 12px 14px;
        border-radius: 14px; font-size: 14px; line-height: 1.5;
        animation: mcwMessageIn 0.3s ease-out;
      }
      @keyframes mcwMessageIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
      }
      .mcw-message-user {
        background: linear-gradient(135deg, #0076A8 0%, #009DAE 100%);
        color: white; align-self: flex-end; border-bottom-right-radius: 4px;
      }
      .mcw-message-assistant {
        background: white; color: #2D3748;
        border: 1px solid #e2e8f0; align-self: flex-start; border-bottom-left-radius: 4px;
      }
      
      .mcw-sources { margin-top: 10px; padding-top: 10px; border-top: 1px solid #e2e8f0; }
      .mcw-sources-label { font-size: 11px; color: #718096; font-weight: 500; margin-bottom: 6px; }
      .mcw-source {
        display: inline-block; font-size: 11px; padding: 4px 8px;
        background: rgba(0, 118, 168, 0.08); color: #0076A8;
        border-radius: 6px; margin-right: 6px; margin-bottom: 4px;
        text-decoration: none;
      }
      .mcw-source:hover { background: rgba(0, 118, 168, 0.15); text-decoration: underline; }
      
      .mcw-typing {
        display: flex; gap: 4px; padding: 12px 14px;
        background: white; border: 1px solid #e2e8f0;
        border-radius: 14px; width: fit-content;
        animation: mcwMessageIn 0.3s ease-out;
      }
      .mcw-typing span {
        width: 8px; height: 8px;
        background: #a0aec0; border-radius: 50%;
        animation: mcwTyping 1.4s infinite ease-in-out;
      }
      .mcw-typing span:nth-child(2) { animation-delay: 0.2s; }
      .mcw-typing span:nth-child(3) { animation-delay: 0.4s; }
      @keyframes mcwTyping {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-4px); }
      }
      
      .mcw-input-area {
        padding: 12px 16px;
        background: white;
        border-top: 1px solid #e2e8f0;
        display: flex; gap: 8px;
      }
      .mcw-input-area input {
        flex: 1; padding: 12px 14px;
        border: 1px solid #e2e8f0; border-radius: 10px;
        font-size: 14px; outline: none;
        transition: border-color 0.2s, box-shadow 0.2s;
      }
      .mcw-input-area input:focus { border-color: #0076A8; box-shadow: 0 0 0 3px rgba(0, 118, 168, 0.1); }
      
      .mcw-send-btn {
        width: 44px; height: 44px;
        background: linear-gradient(135deg, #0076A8 0%, #009DAE 100%);
        border: none; border-radius: 10px; color: white;
        cursor: pointer; display: flex;
        align-items: center; justify-content: center;
        transition: transform 0.2s, box-shadow 0.2s;
      }
      .mcw-send-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0, 118, 168, 0.3); }
      .mcw-send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
      
      .mcw-privacy { text-align: center; font-size: 11px; color: #a0aec0; margin-top: 12px; }
      .mcw-privacy a { color: #0076A8; text-decoration: none; }
      
      .mcw-timestamp { font-size: 10px; color: rgba(255,255,255,0.6); margin-top: 4px; }
      .mcw-message-assistant .mcw-timestamp { color: #a0aec0; }
      
      @media (max-width: 480px) {
        #municipal-chat-widget { bottom: 16px; right: 16px; }
        .mcw-container { width: calc(100vw - 32px); height: calc(100vh - 100px); bottom: 68px; }
        .mcw-toggle { width: 52px; height: 52px; }
      }
    </style>
    
    <button class="mcw-toggle" id="mcw-toggle-btn" aria-label="Open chat">
      <svg class="mcw-toggle-open" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
      </svg>
      <svg class="mcw-toggle-close" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
      </svg>
    </button>
    
    <div class="mcw-container" id="mcw-container"></div>
  `;
  
  document.body.appendChild(widget);
  
  // Elements
  const toggleBtn = document.getElementById('mcw-toggle-btn');
  const container = document.getElementById('mcw-container');
  
  // Toggle widget
  toggleBtn.addEventListener('click', function() {
    state.isOpen = !state.isOpen;
    updateUI();
  });
  
  function updateUI() {
    const openIcon = toggleBtn.querySelector('.mcw-toggle-open');
    const closeIcon = toggleBtn.querySelector('.mcw-toggle-close');
    
    if (state.isOpen) {
      openIcon.style.display = 'none';
      closeIcon.style.display = 'block';
      container.classList.add('open');
      
      if (!state.isInitialized) {
        renderWelcome();
      } else {
        renderChat();
      }
    } else {
      openIcon.style.display = 'block';
      closeIcon.style.display = 'none';
      container.classList.remove('open');
    }
  }
  
  function renderWelcome() {
    container.innerHTML = `
      <div class="mcw-header">
        <div>
          <div class="mcw-header-title">Municipal Chat</div>
          <div class="mcw-header-subtitle">Get instant answers about local services</div>
        </div>
        <button class="mcw-close-btn" id="mcw-header-close">
          <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
          </svg>
        </button>
      </div>
      <div class="mcw-body">
        <div class="mcw-welcome">
          <div class="mcw-welcome-icon">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <h3>Welcome to Municipal Chat</h3>
          <p>Get instant answers about local services, programs, and more</p>
        </div>
        
        <div class="mcw-form">
          <div class="mcw-form-group">
            <label>Your Name <span>*</span></label>
            <input type="text" id="mcw-name" placeholder="Enter your name" />
          </div>
          <div class="mcw-form-group">
            <label>Email <span>(optional)</span></label>
            <input type="email" id="mcw-email" placeholder="Receive a summary of your chat" />
          </div>
          <button class="mcw-form-btn" id="mcw-start-btn">Start Chat</button>
        </div>
        
        <p class="mcw-privacy">By starting a chat, you agree to our <a href="#">Privacy Policy</a></p>
      </div>
    `;
    
    document.getElementById('mcw-start-btn').addEventListener('click', handleStartChat);
    document.getElementById('mcw-header-close').addEventListener('click', function() {
      state.isOpen = false;
      updateUI();
    });
  }
  
  function handleStartChat() {
    const nameInput = document.getElementById('mcw-name');
    const name = nameInput.value.trim();
    
    if (!name) {
      nameInput.focus();
      nameInput.style.borderColor = '#e53e3e';
      return;
    }
    
    const emailInput = document.getElementById('mcw-email');
    const email = emailInput.value.trim();
    
    state.userInfo = { name: name, email: email };
    state.sessionId = 'demo_' + Date.now();
    state.isInitialized = true;
    
    localStorage.setItem('municipal-chat-storage', JSON.stringify({
      state: {
        sessionId: state.sessionId,
        userInfo: state.userInfo
      }
    }));
    
    renderChat();
  }
  
  function renderChat() {
    const name = state.userInfo ? state.userInfo.name : 'User';
    
    let messagesHTML = '';
    
    if (state.messages.length === 0) {
      messagesHTML = `
        <div class="mcw-welcome" style="padding: 24px 0;">
          <p style="color: #2D3748; font-weight: 500;">Hi, ${escapeHTML(name)}! How can we help you today?</p>
          <p style="color: #718096; font-size: 13px; margin-top: 4px;">Ask about garbage, parking, permits, services, and more!</p>
        </div>
      `;
    } else {
      messagesHTML = state.messages.map(function(msg) {
        let content = '<p>' + escapeHTML(msg.content) + '</p>';
        
        if (msg.sources && msg.sources.length > 0) {
          content += '<div class="mcw-sources"><div class="mcw-sources-label">Sources:</div>';
          msg.sources.forEach(function(s) {
            content += '<a href="' + escapeHTML(s.url) + '" class="mcw-source" target="_blank">' + escapeHTML(s.title) + '</a>';
          });
          content += '</div>';
        }
        
        const time = new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        content += '<div class="mcw-timestamp">' + time + '</div>';
        
        return '<div class="mcw-message mcw-message-' + msg.role + '">' + content + '</div>';
      }).join('');
      
      if (state.isTyping) {
        messagesHTML += '<div class="mcw-typing"><span></span><span></span><span></span></div>';
      }
    }
    
    container.innerHTML = `
      <div class="mcw-header">
        <div>
          <div class="mcw-header-title">Municipal Chat</div>
          <div class="mcw-header-subtitle">Hi, ${escapeHTML(name)}!</div>
        </div>
        <button class="mcw-end-btn" id="mcw-end-chat">End Chat</button>
      </div>
      <div class="mcw-body" id="mcw-messages">
        ${messagesHTML}
      </div>
      <div class="mcw-input-area">
        <input type="text" id="mcw-input" placeholder="Ask about municipal services..." />
        <button class="mcw-send-btn" id="mcw-send">
          <svg width="20" height="20" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
          </svg>
        </button>
      </div>
    `;
    
    const body = document.getElementById('mcw-messages');
    body.scrollTop = body.scrollHeight;
    
    const input = document.getElementById('mcw-input');
    const sendBtn = document.getElementById('mcw-send');
    
    sendBtn.addEventListener('click', function() { sendMessage(input); });
    input.addEventListener('keypress', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(input);
      }
    });
    
    document.getElementById('mcw-end-chat').addEventListener('click', handleEndChat);
  }
  
  async function sendMessage(input) {
    const content = input.value.trim();
    if (!content || state.isTyping) return;
    
    const userMsg = {
      role: 'user',
      content: content,
      timestamp: new Date().toISOString()
    };
    state.messages.push(userMsg);
    input.value = '';
    
    state.isTyping = true;
    renderChat();
    
    const newInput = document.getElementById('mcw-input');
    newInput.focus();
    
    let responseContent = DEMO_RESPONSES.default;
    let sources = [
      { title: 'City of Kitchener', url: 'https://www.kitchener.ca' },
      { title: 'City of Waterloo', url: 'https://www.waterloo.ca' }
    ];
    
    try {
      // Call the backend API
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: content,
          session_id: state.sessionId || `widget_${Date.now()}`,
          include_sources: true
        })
      });
      
      if (response.ok) {
        const data = await response.json();
        responseContent = data.answer || data.message || DEMO_RESPONSES.default;
        sources = data.sources || sources;
        state.sessionId = data.session_id || state.sessionId;
      } else {
        console.warn('API error, falling back to demo responses');
      }
    } catch (err) {
      console.warn('Failed to call API, using demo responses:', err.message);
    }
    
    const assistantMsg = {
      role: 'assistant',
      content: responseContent,
      sources: sources,
      timestamp: new Date().toISOString()
    };
    
    state.messages.push(assistantMsg);
    state.isTyping = false;
    
    renderChat();
  }
  
  function handleEndChat() {
    state.isOpen = true;
    state.isInitialized = false;
    state.sessionId = null;
    state.userInfo = null;
    state.messages = [];
    state.isTyping = false;
    
    localStorage.removeItem('municipal-chat-storage');
    renderWelcome();
  }
  
  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
  
  // Initialize UI
  updateUI();
  
  // Expose API for external control
  window.MunicipalChat = {
    open: function() { state.isOpen = true; updateUI(); },
    close: function() { state.isOpen = false; updateUI(); },
    destroy: function() { widget.remove(); }
  };
})();