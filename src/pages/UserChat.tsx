import React, { useState, useRef, useEffect } from 'react';
import {
  apiGetConversations,
  apiGetMessages,
  apiUploadFile,
  apiStartConversation,
  apiSearchUsers,
  apiGetConnectionStatus,
  getCurrentUser,
  getAvatarUrl,
} from '../services/api';
import { getSocket } from '../services/socket';
import StarRating from '../components/StarRating';
import UserProfileModal from '../components/UserProfileModal';
import './UserChat.css';

interface UserChatProps {
  onBack: () => void;
}

const UserChat: React.FC<UserChatProps> = ({ onBack }) => {
  const currentUser = getCurrentUser();
  const [chats, setChats] = useState<any[]>([]);
  const [selectedChat, setSelectedChat] = useState<any | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [input, setInput] = useState('');
  const [search, setSearch] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  // New chat search
  const [showNewChat, setShowNewChat] = useState(false);
  const [userSearch, setUserSearch] = useState('');
  const [userResults, setUserResults] = useState<any[]>([]);
  const [searchingUsers, setSearchingUsers] = useState(false);
  const [viewProfileId, setViewProfileId] = useState<string | null>(null);
  const [isChatLocked, setIsChatLocked] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const typingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const userSearchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    apiGetConversations().then(setChats).catch(console.error);

    // Check if we navigated here specifically to open a chat
    const openChatUserId = localStorage.getItem('openChatUserId');
    if (openChatUserId) {
      localStorage.removeItem('openChatUserId');
      handleStartConversation({ _id: openChatUserId });
    }
  }, []);

  useEffect(() => {
    const socket = getSocket();
    if (!socket) return;

    socket.on('message:new', (msg: any) => {
      if (msg.conversationId === selectedChat?.id) {
        setMessages(prev => [...prev, msg]);
      }
      setChats(prev =>
        prev.map(c =>
          c.id === msg.conversationId
            ? { ...c, lastMessage: msg.text, lastMessageAt: msg.createdAt }
            : c
        )
      );
    });

    socket.on('typing:start', ({ userId }: any) => {
      if (userId !== currentUser?.id) setIsTyping(true);
    });

    socket.on('typing:stop', ({ userId }: any) => {
      if (userId !== currentUser?.id) setIsTyping(false);
    });

    return () => {
      socket.off('message:new');
      socket.off('typing:start');
      socket.off('typing:stop');
    };
  }, [selectedChat, currentUser]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    if (selectedChat?.otherUser) {
      apiGetConnectionStatus(selectedChat.otherUser._id || selectedChat.otherUser.id)
        .then(res => setIsChatLocked(res.status !== 'accepted'))
        .catch(console.error);
    }
  }, [selectedChat]);

  // Search users with debounce
  useEffect(() => {
    if (!userSearch.trim() || userSearch.length < 2) {
      setUserResults([]);
      return;
    }
    if (userSearchTimerRef.current) clearTimeout(userSearchTimerRef.current);
    userSearchTimerRef.current = setTimeout(async () => {
      setSearchingUsers(true);
      try {
        const results = await apiSearchUsers(userSearch);
        setUserResults(results);
      } catch (err) {
        console.error('User search error:', err);
      } finally {
        setSearchingUsers(false);
      }
    }, 400);
  }, [userSearch]);

  const filteredChats = chats.filter(c =>
    c.otherUser?.username?.toLowerCase().includes(search.toLowerCase()) ||
    c.otherUser?.displayName?.toLowerCase().includes(search.toLowerCase())
  );

  const totalUnread = chats.reduce((a, c) => a + (c.unread || 0), 0);

  const isMe = (msg: any) =>
    msg.sender?._id === currentUser?.id || msg.sender === currentUser?.id;

  const handleSelectChat = async (chat: any) => {
    const socket = getSocket();
    if (selectedChat) socket?.emit('conversation:leave', selectedChat.id);
    socket?.emit('conversation:join', chat.id);
    setSelectedChat(chat);
    setShowNewChat(false);
    
    // Proactively clear local unread count
    setChats(prev => prev.map(c => c.id === chat.id ? { ...c, unread: 0 } : c));

    try {
      const msgs = await apiGetMessages(chat.id);
      setMessages(msgs);
    } catch (err) {
      console.error('Load messages error:', err);
    }
  };

  const handleStartConversation = async (user: any) => {
    try {
      const conv = await apiStartConversation(user._id);
      // Shape it the same way the conversations list does
      const shaped = {
        id: conv._id,
        otherUser: conv.participants.find((p: any) => p._id !== currentUser?.id),
        lastMessage: '',
        lastMessageAt: null,
        unread: 0,
      };
      // Add to list if not already there
      setChats(prev => {
        const exists = prev.find(c => c.id === shaped.id);
        return exists ? prev : [shaped, ...prev];
      });
      setUserSearch('');
      setUserResults([]);
      handleSelectChat(shaped);
    } catch (err) {
      console.error('Start conversation error:', err);
    }
  };

  const handleSend = () => {
    const text = input.trim();
    if (!text || !selectedChat) return;
    const socket = getSocket();
    socket?.emit(
      'message:send',
      { conversationId: selectedChat.id, text },
      (res: any) => { if (res?.error) console.error(res.error); }
    );
    socket?.emit('typing:stop', { conversationId: selectedChat.id });
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    setInput('');
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value);
    const socket = getSocket();
    if (!selectedChat || !socket) return;
    socket.emit('typing:start', { conversationId: selectedChat.id });
    if (typingTimerRef.current) clearTimeout(typingTimerRef.current);
    typingTimerRef.current = setTimeout(() => {
      socket.emit('typing:stop', { conversationId: selectedChat.id });
    }, 1500);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !selectedChat) return;
    try {
      const msg = await apiUploadFile(selectedChat.id, file);
      setMessages(prev => [...prev, msg]);
    } catch (err) {
      console.error('File upload error:', err);
    }
    e.target.value = '';
  };

  return (
    <div className="user-chat-root">
      {/* Sidebar */}
      <aside className="chat-sidebar">
        <div className="sidebar-header">
          <div className="sidebar-title-row">
            <h2 className="sidebar-title">Chats</h2>
            {totalUnread > 0 && (
              <span className="sidebar-badge">{totalUnread}</span>
            )}
            {/* New chat button */}
            <button
              className="new-chat-btn"
              onClick={() => { setShowNewChat(v => !v); setUserSearch(''); setUserResults([]); }}
              title="New conversation"
              style={{
                marginLeft: 'auto',
                width: '30px',
                height: '30px',
                borderRadius: '50%',
                background: showNewChat ? 'var(--clr-primary-light)' : 'var(--clr-surface-2)',
                color: showNewChat ? 'white' : 'var(--clr-text-muted)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1.5px solid var(--clr-border)',
                cursor: 'pointer',
                flexShrink: 0,
                transition: 'all 0.2s',
              }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
            </button>
          </div>

          {/* New chat search panel */}
          {showNewChat && (
            <div style={{ marginBottom: '0.8rem' }}>
              <input
                type="text"
                placeholder="Search by username..."
                value={userSearch}
                onChange={e => setUserSearch(e.target.value)}
                autoFocus
                style={{
                  width: '100%',
                  padding: '0.6rem 0.9rem',
                  background: 'var(--clr-surface-2)',
                  border: '1.5px solid var(--clr-primary-light)',
                  borderRadius: 'var(--radius-full)',
                  fontSize: '0.85rem',
                  color: 'var(--clr-text-primary)',
                  outline: 'none',
                  boxSizing: 'border-box',
                }}
              />
              {searchingUsers && (
                <p style={{ fontSize: '0.8rem', color: 'var(--clr-text-muted)', padding: '0.4rem 0.2rem' }}>
                  Searching...
                </p>
              )}
              {userResults.length > 0 && (
                <div style={{
                  marginTop: '0.4rem',
                  background: 'var(--clr-surface)',
                  border: '1px solid var(--clr-border)',
                  borderRadius: 'var(--radius-md)',
                  overflow: 'hidden',
                }}>
                  {userResults.map(user => (
                    <div
                      key={user._id}
                      onClick={() => {
                        setViewProfileId(user._id);
                      }}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.7rem',
                        padding: '0.65rem 0.9rem',
                        cursor: 'pointer',
                        transition: 'background 0.15s',
                      }}
                      onMouseEnter={e => (e.currentTarget.style.background = 'var(--clr-surface-2)')}
                      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                    >
                      <img
                        src={getAvatarUrl(user.avatarUrl) || `https://api.dicebear.com/7.x/thumbs/svg?seed=${user.username}`}
                        alt={user.username}
                        width="34"
                        height="34"
                        style={{ borderRadius: '50%' }}
                      />
                      <div>
                        <div style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--clr-text-primary)' }}>
                          {user.displayName || user.username}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--clr-text-muted)', display: 'flex', alignItems: 'center', gap: '0.35rem', marginTop: '0.15rem' }}>
                          @{user.username}
                          <span style={{opacity: 0.3}}>•</span>
                          <StarRating value={user.cloutScore || 0} readOnly size={12} />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              {!searchingUsers && userSearch.length >= 2 && userResults.length === 0 && (
                <p style={{ fontSize: '0.8rem', color: 'var(--clr-text-muted)', padding: '0.4rem 0.2rem' }}>
                  No users found
                </p>
              )}
            </div>
          )}

          <div className="sidebar-search-wrap">
            <svg className="sidebar-search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              className="sidebar-search"
              type="text"
              placeholder="Search"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            <button className="sidebar-mic-btn" aria-label="Voice search">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
            </button>
          </div>
        </div>

        <div className="chat-list">
          {filteredChats.length === 0 ? (
            <p style={{ padding: '1rem', fontSize: '0.85rem', color: 'var(--clr-text-muted)', textAlign: 'center' }}>
              No conversations yet.{' '}
              <span
                style={{ color: 'var(--clr-primary-light)', cursor: 'pointer', fontWeight: 600 }}
                onClick={() => setShowNewChat(true)}
              >
                Start one!
              </span>
            </p>
          ) : (
            filteredChats.map(chat => (
              <div
                key={chat.id}
                className={`chat-list-item ${selectedChat?.id === chat.id ? 'chat-list-item--active' : ''}`}
                onClick={() => handleSelectChat(chat)}
              >
                <div className="chat-item-avatar">
                  <img
                    src={
                      getAvatarUrl(chat.otherUser?.avatarUrl) ||
                      `https://api.dicebear.com/7.x/thumbs/svg?seed=${chat.otherUser?.username}`
                    }
                    alt={chat.otherUser?.username}
                    width="44"
                    height="44"
                  />
                </div>
                <div className="chat-item-info">
                  <div className="chat-item-top">
                    <span className="chat-item-name">
                      {chat.otherUser?.displayName || chat.otherUser?.username}
                    </span>
                    <span className="chat-item-time">
                      {chat.lastMessageAt
                        ? new Date(chat.lastMessageAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        : ''}
                    </span>
                  </div>
                  <span className="chat-item-preview">{chat.lastMessage || 'No messages yet'}</span>
                </div>
                {chat.unread > 0 && (
                  <span className="chat-unread">{chat.unread}</span>
                )}
              </div>
            ))
          )}
        </div>
      </aside>

      {/* Main chat area */}
      <main className="chat-main">
        {selectedChat ? (
          <>
            <header className="chat-main-header">
              <button className="back-btn" onClick={() => setSelectedChat(null)} aria-label="Back">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="15 18 9 12 15 6"/>
                </svg>
              </button>
              <div className="chat-main-header-identity">
                <div 
                  className="chat-header-avatar-wrap" 
                  onClick={() => setViewProfileId(selectedChat.otherUser?._id || selectedChat.otherUser?.id)} 
                  style={{ cursor: 'pointer' }}
                >
                  <img
                    src={
                      getAvatarUrl(selectedChat.otherUser?.avatarUrl) ||
                      `https://api.dicebear.com/7.x/thumbs/svg?seed=${selectedChat.otherUser?.username}`
                    }
                    alt={selectedChat.otherUser?.username}
                    width="38"
                    height="38"
                    className="chat-header-avatar"
                  />
                </div>
                <div>
                  <h3 
                    className="chat-header-name" 
                    onClick={() => setViewProfileId(selectedChat.otherUser?._id || selectedChat.otherUser?.id)} 
                    style={{ cursor: 'pointer' }}
                  >
                    {selectedChat.otherUser?.displayName || selectedChat.otherUser?.username}
                  </h3>
                </div>
              </div>
              <div className="chat-header-actions">
                <button className="chat-action-btn" aria-label="Video call">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polygon points="23 7 16 12 23 17 23 7"/>
                    <rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>
                  </svg>
                </button>
                <button className="chat-action-btn" aria-label="More options">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="5" r="1"/>
                    <circle cx="12" cy="12" r="1"/>
                    <circle cx="12" cy="19" r="1"/>
                  </svg>
                </button>
              </div>
            </header>

            <div className="chat-messages-area">
              {messages.map((msg, i) => (
                <div
                  key={msg._id || msg.id || i}
                  className={`message-row message-row--${isMe(msg) ? 'me' : 'other'}`}
                  style={{ animationDelay: `${i * 0.04}s` }}
                >
                  {!isMe(msg) && (
                    <div className="msg-avatar">
                      <img
                        src={
                          getAvatarUrl(msg.sender?.avatarUrl) ||
                          `https://api.dicebear.com/7.x/thumbs/svg?seed=${msg.sender?.username}`
                        }
                        alt={msg.sender?.username}
                        width="34"
                        height="34"
                      />
                    </div>
                  )}
                  <div className={`message-bubble message-bubble--${isMe(msg) ? 'me' : 'other'}`}>
                    {msg.file ? (
                      <a
                        href={`http://localhost:5000${msg.file.url}`}
                        target="_blank"
                        rel="noreferrer"
                        style={{ color: 'var(--clr-primary-light)', fontSize: '0.88rem' }}
                      >
                        📎 {msg.file.originalName}
                      </a>
                    ) : (
                      <p className="message-text">{msg.text}</p>
                    )}
                    <span className="message-time">
                      {msg.createdAt
                        ? new Date(msg.createdAt).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                        : msg.timestamp || ''}
                    </span>
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="message-row message-row--other">
                  <div
                    className="message-bubble message-bubble--other"
                    style={{ padding: '0.9rem 1.1rem', display: 'flex', gap: '0.3rem', alignItems: 'center' }}
                  >
                    <span className="typing-dot" />
                    <span className="typing-dot" style={{ animationDelay: '0.15s' }} />
                    <span className="typing-dot" style={{ animationDelay: '0.3s' }} />
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </div>

            {isChatLocked ? (
              <div className="chat-locked-bar" style={{ padding: '1.2rem', textAlign: 'center', color: 'var(--clr-text-muted)', background: 'var(--clr-surface-2)', borderTop: '1px solid var(--clr-border)', fontSize: '0.9rem', fontWeight: 500 }}>
                🔒 You must be connected with this user to send messages.
              </div>
            ) : (
              <div className="chat-input-bar">
                <input
                  ref={fileInputRef}
                  type="file"
                  style={{ display: 'none' }}
                  onChange={handleFileChange}
                />
                <button className="input-icon-btn" aria-label="Emoji">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M8 14s1.5 2 4 2 4-2 4-2"/>
                    <line x1="9" y1="9" x2="9.01" y2="9"/>
                    <line x1="15" y1="9" x2="15.01" y2="9"/>
                  </svg>
                </button>
                <button
                  className="input-icon-btn"
                  aria-label="Attach file"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
                  </svg>
                </button>
                <input
                  className="chat-input"
                  type="text"
                  placeholder="Type a message"
                  value={input}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                />
                <button
                  className={`send-btn ${input.trim() ? 'send-btn--active' : ''}`}
                  onClick={handleSend}
                  disabled={!input.trim()}
                  aria-label="Send message"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="22" y1="2" x2="11" y2="13"/>
                    <polygon points="22 2 15 22 11 13 2 9 22 2"/>
                  </svg>
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="chat-empty-state">
            <div className="chat-empty-illustration">
              <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="var(--clr-border)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                <circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
              </svg>
            </div>
            <h2 className="chat-empty-title">Happy Collaborations</h2>
            <p className="chat-empty-desc">Select a conversation or start a new one</p>
            <button
              onClick={() => setShowNewChat(true)}
              style={{
                marginTop: '1rem',
                padding: '0.7rem 1.6rem',
                background: 'linear-gradient(135deg, var(--clr-primary-light), var(--clr-accent))',
                color: 'white',
                borderRadius: 'var(--radius-full)',
                fontFamily: 'var(--font-display)',
                fontWeight: 600,
                fontSize: '0.9rem',
                cursor: 'pointer',
                border: 'none',
              }}
            >
              + New Conversation
            </button>
            <button className="back-btn-main" onClick={onBack}>
              ← Back to dashboard
            </button>
          </div>
        )}
      </main>

      {/* User Profile Modal */}
      {viewProfileId && (
        <UserProfileModal 
          userId={viewProfileId} 
          onClose={() => setViewProfileId(null)} 
          onMessageClick={() => {
            handleStartConversation({ _id: viewProfileId });
            setViewProfileId(null);
          }}
        />
      )}
    </div>
  );
};

export default UserChat;