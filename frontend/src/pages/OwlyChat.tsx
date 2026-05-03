import React, { useState, useRef, useEffect } from 'react';
import OwlIcon from '../components/OwlIcon';
import { mockOwlyMessages, Message, AVATARS } from '../data/mockData';
import './OwlyChat.css';

interface OwlyChatProps {
  onBack: () => void;
}

const OwlyChat: React.FC<OwlyChatProps> = ({ onBack }) => {
  const [messages, setMessages] = useState<Message[]>(mockOwlyMessages);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [threadId, setThreadId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: 'me',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      avatar: AVATARS.me,
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      // 1. Prepare history for the backend
      const history = messages
        .filter(m => m.id !== "1") // Skip the welcome message for model context if you prefer
        .map(m => ({
          role: m.sender === 'me' ? 'user' : 'bot',
          content: m.text
        }));

      // 2. Call our unified FastAPI backend
      const response = await fetch('http://localhost:5000/api/owly/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: text,
          history: history,
          thread_id: threadId
        }),
      });

      if (!response.ok) throw new Error('Failed to connect to Owly');

      // 3. Handle thread_id from headers
      const newThreadId = response.headers.get('X-Thread-ID');
      if (newThreadId) setThreadId(newThreadId);

      setIsTyping(false);

      // 4. Handle Streaming Response
      const reader = response.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      const owlyMsgId = (Date.now() + 1).toString();
      
      // Initialize an empty message from Owly
      const initialOwlyMsg: Message = {
        id: owlyMsgId,
        sender: 'owly',
        text: '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      
      setMessages(prev => [...prev, initialOwlyMsg]);

      let fullText = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;

        // Update the last message (the Owly one we just added) with the new text
        setMessages(prev => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (updated[lastIdx].id === owlyMsgId) {
            updated[lastIdx] = { ...updated[lastIdx], text: fullText };
          }
          return updated;
        });
      }

    } catch (error) {
      console.error('Owly Error:', error);
      setIsTyping(false);
      const errorMsg: Message = {
        id: 'error-' + Date.now(),
        sender: 'owly',
        text: "Hoot! I'm having trouble connecting to my database right now. Please make sure the UpClout backend is running.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages(prev => [...prev, errorMsg]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="owly-chat-root">
      {/* Header */}
      <header className="owly-chat-header">
        <button className="back-btn" onClick={onBack} aria-label="Go back">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="15 18 9 12 15 6"/>
          </svg>
        </button>
        <div className="owly-chat-header-identity">
          <OwlIcon size={32} />
          <div>
            <h2 className="owly-chat-title">Ask Owly</h2>
            <span className="owly-chat-subtitle">your AI assistant</span>
          </div>
        </div>
        <div className="owly-header-status">
          <span className="status-dot" />
          <span>Online</span>
        </div>
      </header>

      {/* Messages */}
      <div className="owly-messages-area">
        {messages.map((msg, i) => (
          <div
            key={msg.id}
            className={`message-row message-row--${msg.sender}`}
            style={{ animationDelay: `${i * 0.05}s` }}
          >
            {(msg.sender === 'owly') && (
              <div className="msg-avatar msg-avatar--owly">
                <OwlIcon size={32} />
              </div>
            )}

            <div className={`message-bubble message-bubble--${msg.sender}`}>
              <p className="message-text">{msg.text}</p>
              <span className="message-time">{msg.timestamp}</span>
            </div>

            {/* User avatar removed as requested */}
          </div>
        ))}

        {/* Typing indicator */}
        {isTyping && (
          <div className="message-row message-row--owly">
            <div className="msg-avatar msg-avatar--owly">
              <OwlIcon size={32} />
            </div>
            <div className="message-bubble message-bubble--owly typing-bubble">
              <span className="typing-dot" />
              <span className="typing-dot" style={{ animationDelay: '0.15s' }} />
              <span className="typing-dot" style={{ animationDelay: '0.3s' }} />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="owly-input-bar">
        <button className="input-icon-btn" aria-label="Emoji">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>
          </svg>
        </button>
        <button className="input-icon-btn" aria-label="Attach">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
          </svg>
        </button>
        <input
          className="chat-input"
          type="text"
          placeholder="Type a message"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          className={`send-btn ${input.trim() ? 'send-btn--active' : ''}`}
          onClick={handleSend}
          disabled={!input.trim()}
          aria-label="Send message"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
        </button>
      </div>
    </div>
  );
};

export default OwlyChat;
