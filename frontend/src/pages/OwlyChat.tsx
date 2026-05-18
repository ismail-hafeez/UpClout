import React, { useState, useRef, useEffect } from 'react';
import OwlIcon from '../components/OwlIcon';
import { apiGetOwlyConversations, apiGetOwlyMessages, apiDeleteOwlyConversation, apiOwlyChat } from '../services/api';
import './OwlyChat.css';

interface OwlyChatProps {
  onBack: () => void;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ConversationSummary {
  _id: string;
  title: string;
  updated_at: string;
  last_message_preview: string;
}

const WELCOME_MESSAGE: ChatMessage = {
  id: 'welcome',
  role: 'assistant',
  content: "Hoot! 🦉 I'm Owly, your AI talent scout. I already know who you are — let's find your perfect match. What are you looking for today?",
  timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
};

const OwlyChat: React.FC<OwlyChatProps> = ({ onBack }) => {
  // Sidebar state
  const [conversations, setConversations] = useState<ConversationSummary[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([WELCOME_MESSAGE]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const loadConversations = async () => {
    try {
      const convs = await apiGetOwlyConversations();
      setConversations(convs);
    } catch (err) {
      console.error('Failed to load Owly conversations:', err);
    }
  };

  const selectConversation = async (convId: string) => {
    if (convId === activeConvId) return;
    setLoadingHistory(true);
    setActiveConvId(convId);
    try {
      const data = await apiGetOwlyMessages(convId);
      const loaded: ChatMessage[] = data.messages.map((m: any, i: number) => ({
        id: `${convId}-${i}`,
        role: m.role,
        content: m.content,
        timestamp: m.timestamp
          ? new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          : '',
      }));
      setMessages(loaded.length > 0 ? loaded : [WELCOME_MESSAGE]);
    } catch (err) {
      console.error('Failed to load conversation:', err);
      setMessages([WELCOME_MESSAGE]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const startNewConversation = () => {
    setActiveConvId(null);
    setMessages([WELCOME_MESSAGE]);
    setInput('');
  };

  const deleteConversation = async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await apiDeleteOwlyConversation(convId);
      setConversations(prev => prev.filter(c => c._id !== convId));
      if (activeConvId === convId) {
        startNewConversation();
      }
    } catch (err) {
      console.error('Failed to delete conversation:', err);
    }
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || isTyping) return;

    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    try {
      const response = await apiOwlyChat(text, activeConvId);

      if (!response.ok) throw new Error('Failed to connect to Owly');

      // Get conversation ID from response headers
      const newConvId = response.headers.get('X-Conversation-ID');
      if (newConvId && !activeConvId) {
        setActiveConvId(newConvId);
      }

      setIsTyping(false);

      // Handle streaming response
      const reader = response.body?.getReader();
      if (!reader) return;

      const decoder = new TextDecoder();
      const owlyMsgId = (Date.now() + 1).toString();

      const initialOwlyMsg: ChatMessage = {
        id: owlyMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages(prev => [...prev, initialOwlyMsg]);

      let fullText = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;

        setMessages(prev => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (updated[lastIdx].id === owlyMsgId) {
            updated[lastIdx] = { ...updated[lastIdx], content: fullText };
          }
          return updated;
        });
      }

      // Refresh sidebar after successful exchange
      loadConversations();

    } catch (error) {
      console.error('Owly Error:', error);
      setIsTyping(false);
      const errorMsg: ChatMessage = {
        id: 'error-' + Date.now(),
        role: 'assistant',
        content: "Hoot! I'm having trouble connecting right now. Please make sure the UpClout backend is running.",
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

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    const now = new Date();
    const diff = now.getTime() - d.getTime();
    if (diff < 86400000) return 'Today';
    if (diff < 172800000) return 'Yesterday';
    return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  return (
    <div className="owly-chat-root">
      {/* Sidebar */}
      <aside className={`owly-sidebar ${sidebarOpen ? 'owly-sidebar--open' : 'owly-sidebar--closed'}`}>
        <div className="owly-sidebar-header">
          <h3 className="owly-sidebar-title">Conversations</h3>
          <button className="owly-new-chat-btn" onClick={startNewConversation} title="New chat">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
          </button>
        </div>
        <div className="owly-sidebar-list">
          {conversations.length === 0 && (
            <div className="owly-sidebar-empty">
              <OwlIcon size={28} />
              <span>No conversations yet</span>
            </div>
          )}
          {conversations.map(conv => (
            <div
              key={conv._id}
              className={`owly-sidebar-item ${activeConvId === conv._id ? 'owly-sidebar-item--active' : ''}`}
              onClick={() => selectConversation(conv._id)}
            >
              <div className="owly-sidebar-item-content">
                <span className="owly-sidebar-item-title">{conv.title}</span>
                <span className="owly-sidebar-item-date">{formatDate(conv.updated_at)}</span>
              </div>
              <button
                className="owly-sidebar-delete"
                onClick={(e) => deleteConversation(conv._id, e)}
                title="Delete conversation"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                </svg>
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="owly-chat-main">
        {/* Header */}
        <header className="owly-chat-header">
          <div className="owly-header-left">
            <button className="back-btn" onClick={onBack} aria-label="Go back">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polyline points="15 18 9 12 15 6"/>
              </svg>
            </button>
            <button
              className="owly-sidebar-toggle"
              onClick={() => setSidebarOpen(prev => !prev)}
              title={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/>
              </svg>
            </button>
          </div>
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
          {loadingHistory && (
            <div className="owly-loading-history">
              <div className="owly-loading-spinner" />
              <span>Loading conversation...</span>
            </div>
          )}

          {!loadingHistory && messages.map((msg, i) => (
            <div
              key={msg.id}
              className={`message-row message-row--${msg.role === 'user' ? 'me' : 'owly'}`}
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              {msg.role === 'assistant' && (
                <div className="msg-avatar msg-avatar--owly">
                  <OwlIcon size={32} />
                </div>
              )}

              <div className={`message-bubble message-bubble--${msg.role === 'user' ? 'me' : 'owly'}`}>
                <p className="message-text">{msg.content}</p>
                <span className="message-time">{msg.timestamp}</span>
              </div>
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
          <input
            className="chat-input"
            type="text"
            placeholder="Type a message..."
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
          />
          <button
            className={`send-btn ${input.trim() ? 'send-btn--active' : ''}`}
            onClick={handleSend}
            disabled={!input.trim() || isTyping}
            aria-label="Send message"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default OwlyChat;
