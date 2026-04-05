import React, { useState, useEffect, useRef } from 'react';
import OwlIcon from '../components/OwlIcon';
import CampaignIcon from '../components/CampaignIcon';
import MessageIcon from '../components/MessageIcon';
import BellIcon from '../components/BellIcon';
import { getCurrentUser, getAvatarUrl, apiSearchUsers, apiGetConnectionRequests, apiAcceptConnectionRequest, apiRejectConnectionRequest, apiGetCollaborations, apiMarkCollaborationsSeen, apiGetBrandStats, apiGetBrandRecommendations } from '../services/api';
import EditProfileModal from '../components/EditProfileModal';
import UserProfileModal from '../components/UserProfileModal';
import StarRating from '../components/StarRating';
import './MainPage.css';

import AnalyticsDashboard from './AnalyticsDashboard';

type ActiveTab = 'discover' | 'owly' | 'chats' | 'campaigns' | 'analytics';

// Removed inline CampaignIcon for pretty component import

interface MainPageProps {
  onNavigate: (page: string, params?: any) => void;
  onBack: () => void;
  unreadCount: number;
  theme: 'dark' | 'light';
  onToggleTheme: () => void;
}

const MainPage: React.FC<MainPageProps> = ({ onNavigate, onBack, unreadCount, theme, onToggleTheme }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('discover');
  const [searchQuery, setSearchQuery] = useState('');
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [showEditProfile, setShowEditProfile] = useState(false);
  const [currentUser, setCurrentUserState] = useState(getCurrentUser());
  const [userResults, setUserResults] = useState<any[]>([]);
  const [searchingUsers, setSearchingUsers] = useState(false);
  const [viewProfileId, setViewProfileId] = useState<string | null>(null);
  const searchTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [reqs, setReqs] = useState<any[]>([]);
  const [reqsOpen, setReqsOpen] = useState(false);
  const [campaignInviteCount, setCampaignInviteCount] = useState(0);
  const [brandStats, setBrandStats] = useState<{ followers: number, following: number, posts: number } | null>(null);
  const [recommendedInfluencers, setRecommendedInfluencers] = useState<any[]>([]);
  const user = getCurrentUser();

  // ---- Smart navbar: hide on scroll-down, show on scroll-up ----
  const [navHidden, setNavHidden] = useState(false);
  const [navScrolled, setNavScrolled] = useState(false);
  const lastScrollY = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentY = window.scrollY;
      const delta = currentY - lastScrollY.current;

      // Hide when scrolling down past 60px, show when scrolling up
      if (delta > 8 && currentY > 60) {
        setNavHidden(true);
      } else if (delta < -5) {
        setNavHidden(false);
      }

      // Scrolled state for stronger glass effect
      setNavScrolled(currentY > 30);
      lastScrollY.current = currentY;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    apiGetConnectionRequests().then(setReqs).catch(console.error);
    const intv = setInterval(() => apiGetConnectionRequests().then(setReqs).catch(console.error), 15000);

    // Also fetch campaign invites for influencers
    const fetchDashboardData = async () => {
      // 1. Stats for everyone
      try {
        const stats = await apiGetBrandStats();
        if (stats && Object.keys(stats).length > 0) {
          setBrandStats(stats);
        }
      } catch (err) { console.error(err); }

      // 2. Recommendations for everyone
      try {
        const recs = await apiGetBrandRecommendations();
        if (recs && recs.length > 0) {
          setRecommendedInfluencers(recs);
        }
      } catch (err) { console.error(err); }

      // 3. Campaign invites specifically for influencers
      if (user?.userType === 'Influencer') {
        try {
          const collabs = await apiGetCollaborations();
          const newCount = collabs.filter((c: any) => c.isNew).length;
          setCampaignInviteCount(newCount);
        } catch (err) { console.error(err); }
      }
    };
    fetchDashboardData();
    const invIntv = setInterval(fetchDashboardData, 10000);

    return () => {
      clearInterval(intv);
      clearInterval(invIntv);
    };
  }, []);

  const handleAcceptReq = async (id: string) => {
    await apiAcceptConnectionRequest(id);
    setReqs(prev => prev.filter(r => r._id !== id));
  };
  const handleRejectReq = async (id: string) => {
    await apiRejectConnectionRequest(id);
    setReqs(prev => prev.filter(r => r._id !== id));
  };

  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setUserResults([]);
      return;
    }
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    searchTimerRef.current = setTimeout(async () => {
      setSearchingUsers(true);
      try {
        const results = await apiSearchUsers(searchQuery);
        setUserResults(results);
      } catch (err) {
        console.error('Search error:', err);
      } finally {
        setSearchingUsers(false);
      }
    }, 300);
  }, [searchQuery]);

  const handleMessageClick = (userId: string) => {
    localStorage.setItem('openChatUserId', userId);
    setViewProfileId(null);
    onNavigate('chats');
  };
  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
  };

  // ---- Particles (Landing style) ----
  const particles = Array.from({ length: 25 }, (_, i) => {
    const left = Math.random() * 100;
    const size = 2 + Math.random() * 3;
    const dur = 8 + Math.random() * 14;
    const delay = Math.random() * 10;
    const opacity = 0.2 + Math.random() * 0.4;
    return (
      <div
        key={i}
        className="lp-particle"
        style={{
          left: `${left}%`,
          width: `${size}px`,
          height: `${size}px`,
          animationDuration: `${dur}s`,
          animationDelay: `${delay}s`,
          opacity,
        }}
      />
    );
  });

  return (
    <div className="main-root">

      {/* Floating particles (Landing style) */}
      <div className="lp-particles">{particles}</div>

      {/* Navbar */}
      <nav className={`main-nav${navHidden ? ' main-nav--hidden' : ''}${navScrolled ? ' main-nav--scrolled' : ''}`}>
        <div className="nav-brand" style={{ display: 'flex', flexDirection: 'column' }}>
          <div>
            <span className="brand-up">Up</span>
            <span className="brand-clout">Clout</span>
          </div>
          <span style={{ fontSize: '0.6rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--clr-text-primary)', fontWeight: 600, marginTop: '-0.1rem' }}>
            {currentUser?.userType || 'Influencer'} Dashboard
          </span>
        </div>

        <div style={{ position: 'relative', flex: 1, maxWidth: '350px', margin: '0 1rem' }}>
          <form className="nav-search" onSubmit={handleSearch} style={{ margin: 0, maxWidth: 'none' }}>
            <div className="search-inner">
              <svg className="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
              <input
                type="text"
                className="search-input"
                placeholder="Search influencers or brands..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button
                  type="button"
                  className="search-clear"
                  onClick={() => { setSearchQuery(''); setUserResults([]); }}
                  aria-label="Clear search"
                >
                  ×
                </button>
              )}
              <button type="submit" className="search-btn" aria-label="Search" />
            </div>
          </form>

          {searchQuery.trim().length >= 2 && (
            <div className="glass-search-dropdown" style={{
              position: 'absolute', top: '100%', left: 0, right: 0, marginTop: '0.5rem',
              zIndex: 100, overflow: 'hidden'
            }}>
              {searchingUsers ? (
                <div style={{ padding: '1rem', color: 'var(--clr-text-muted)', fontSize: '0.9rem', textAlign: 'center' }}>Searching...</div>
              ) : userResults.length > 0 ? (
                userResults.map(user => (
                  <div
                    key={user._id}
                    onClick={() => {
                      onNavigate('profile', { username: user.username });
                      setSearchQuery('');
                      setUserResults([]);
                    }}
                    style={{
                      display: 'flex', alignItems: 'center', gap: '0.8rem', padding: '0.75rem 1rem',
                      cursor: 'pointer', borderBottom: '1px solid var(--clr-border)', transition: 'background 0.15s'
                    }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--clr-surface-2)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <img
                      src={getAvatarUrl(user.avatarUrl) || `https://api.dicebear.com/7.x/thumbs/svg?seed=${user.username}`}
                      alt={user.username}
                      style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover', border: '1px solid var(--clr-border)' }}
                    />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '0.95rem', fontWeight: 600, color: 'var(--clr-text-primary)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        {user.displayName || user.username}
                        {user.is_pg && (
                          <span style={{ fontSize: '0.65rem', padding: '0.1rem 0.4rem', borderRadius: '4px', background: user.userType === 'Brand' ? 'rgba(37, 99, 235, 0.1)' : 'rgba(139, 92, 246, 0.1)', color: user.userType === 'Brand' ? 'var(--clr-primary)' : '#8b5cf6', fontWeight: 700, textTransform: 'uppercase' }}>
                            {user.userType}
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--clr-text-muted)', display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '0.2rem' }}>
                        @{user.username}
                        <span style={{ opacity: 0.3 }}>•</span>
                        {user.is_pg ? (
                          <span style={{ fontWeight: 600 }}>{user.followers?.toLocaleString() || 0} Followers</span>
                        ) : (
                          <StarRating value={user.cloutScore || 0} readOnly size={12} />
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ padding: '1rem', color: 'var(--clr-text-muted)', fontSize: '0.9rem', textAlign: 'center' }}>No users found</div>
              )}
            </div>
          )}
        </div>

        <div className="nav-actions">
          <button className="nav-icon-btn nav-owly-btn" onClick={() => onNavigate('owly')} title="Ask Owly">
            <OwlIcon size={26} />
          </button>
          <button className="nav-icon-btn" onClick={() => {
            if (campaignInviteCount > 0) {
              apiMarkCollaborationsSeen();
              setCampaignInviteCount(0);
            }
            onNavigate('campaigns');
          }} title="Campaigns">
            <CampaignIcon size={25} />
            {campaignInviteCount > 0 && <span className="nav-badge" style={{ background: '#ef4444' }}>{campaignInviteCount}</span>}
          </button>
          <button className="nav-icon-btn" onClick={() => onNavigate('chats')} title="Messages">
            <MessageIcon size={25} />
            {unreadCount > 0 && <span className="nav-badge">{unreadCount}</span>}
          </button>

          <button className={`nav-icon-btn ${activeTab === 'analytics' ? 'nav-icon-btn--active' : ''}`} onClick={() => setActiveTab('analytics')} title="Analytics">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="20" x2="18" y2="10" />
              <line x1="12" y1="20" x2="12" y2="4" />
              <line x1="6" y1="20" x2="6" y2="14" />
            </svg>
          </button>

          {/* Notifications Bell */}
          <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            <button className="nav-icon-btn" onClick={() => setReqsOpen(v => !v)} title="Notifications">
              <BellIcon size={25} />
              {reqs.length > 0 && <span className="nav-badge" style={{ background: '#ef4444' }}>{reqs.length}</span>}
            </button>

            {reqsOpen && (
              <>
                <div className="nav-dropdown-backdrop" onClick={() => setReqsOpen(false)} />
                <div className="nav-dropdown" style={{ width: '310px', padding: '1.2rem', right: '-0.5rem' }}>
                  <h4 style={{ margin: '0 0 1rem 0', color: 'var(--clr-text-primary)' }}>Connection Requests</h4>
                  {reqs.length === 0 ? (
                    <p style={{ color: 'var(--clr-text-muted)', fontSize: '0.9rem', textAlign: 'center' }}>No pending requests.</p>
                  ) : (
                    reqs.map(r => (
                      <div key={r._id} style={{ display: 'flex', gap: '0.8rem', alignItems: 'center', marginBottom: '1.2rem' }}>
                        <img src={getAvatarUrl(r.requester?.avatarUrl) || `https://api.dicebear.com/7.x/thumbs/svg?seed=${r.requester?.username}`} style={{ width: '40px', height: '40px', borderRadius: '50%', objectFit: 'cover' }} />
                        <div style={{ flex: 1 }}>
                          <span style={{ fontSize: '0.9rem', fontWeight: 600, color: 'var(--clr-text-primary)' }}>{r.requester?.displayName || r.requester?.username}</span>
                          <span style={{ display: 'block', fontSize: '0.75rem', color: 'var(--clr-text-muted)', marginBottom: '0.4rem' }}>wants to connect.</span>
                          <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button onClick={() => handleAcceptReq(r._id)} style={{ flex: 1, padding: '0.45rem', background: 'var(--clr-primary-light)', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>Accept</button>
                            <button onClick={() => handleRejectReq(r._id)} style={{ flex: 1, padding: '0.45rem', background: 'var(--clr-surface-2)', color: 'var(--clr-text-primary)', border: 'none', borderRadius: '8px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>Ignore</button>
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </>
            )}
          </div>
          {/* User avatar + dropdown */}
          <div className="nav-avatar-wrap">
            <button
              className="nav-avatar"
              onClick={() => setDropdownOpen(v => !v)}
              title="Account"
            >
              {currentUser?.avatarUrl ? (
                <img src={getAvatarUrl(currentUser.avatarUrl)} alt="avatar" style={{ width: 38, height: 38, borderRadius: '50%', objectFit: 'cover' }} />
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              )}
            </button>

            {dropdownOpen && (
              <>
                <div className="nav-dropdown-backdrop" onClick={() => setDropdownOpen(false)} />
                <div className="nav-dropdown">
                  {/* User info */}
                  <div className="nav-dropdown-user">
                    <div className="nav-dropdown-avatar">
                      {currentUser?.avatarUrl ? (
                        <img src={getAvatarUrl(currentUser.avatarUrl)} alt="avatar" style={{ width: 38, height: 38, borderRadius: '50%', objectFit: 'cover' }} />
                      ) : (
                        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                          <circle cx="12" cy="7" r="4" />
                        </svg>
                      )}
                    </div>
                    <div className="nav-dropdown-info">
                      <span className="nav-dropdown-name">{currentUser?.displayName || currentUser?.username || 'User'}</span>
                      <span className="nav-dropdown-username">@{currentUser?.username || 'user'}</span>
                    </div>
                  </div>

                  <div className="nav-dropdown-divider" />

                  {/* Edit Profile */}
                  <button className="nav-dropdown-item" onClick={() => { setDropdownOpen(false); setShowEditProfile(true); }}>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                    </svg>
                    Edit Profile
                  </button>

                  {/* Theme toggle */}
                  <button className="nav-dropdown-item" onClick={() => { onToggleTheme(); setDropdownOpen(false); }}>
                    {theme === 'dark' ? (
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="5" />
                        <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                        <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                      </svg>
                    ) : (
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                      </svg>
                    )}
                    Switch to {theme === 'dark' ? 'Light' : 'Dark'} Mode
                  </button>

                  <div className="nav-dropdown-divider" />

                  {/* Logout */}
                  <button className="nav-dropdown-logout" onClick={onBack}>
                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                      <polyline points="16 17 21 12 16 7" />
                      <line x1="21" y1="12" x2="9" y2="12" />
                    </svg>
                    Log out
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <main className="main-hero">
        {activeTab === 'analytics' ? (
          <AnalyticsDashboard />
        ) : (
          <>
            {/* Welcome User Slogan */}
            <div className="hero-content" style={{ marginTop: '1rem' }}>
              <h1 className="hero-title" style={{ whiteSpace: 'nowrap' }}>
                Welcome, <span className="hero-title-accent">@{currentUser?.username || 'user'}</span>!
              </h1>

              {brandStats && (
                <div className="hero-stats" style={{ marginTop: '2rem', justifyContent: 'center' }}>
                  <div className="stat-card">
                    <span className="stat-number">{brandStats.followers?.toLocaleString() || 0}</span>
                    <span className="stat-label">Followers</span>
                  </div>
                  <div className="stat-divider"></div>
                  <div className="stat-card">
                    <span className="stat-number">{brandStats.following?.toLocaleString() || 0}</span>
                    <span className="stat-label">Following</span>
                  </div>
                  <div className="stat-divider"></div>
                  <div className="stat-card">
                    <span className="stat-number">{brandStats.posts?.toLocaleString() || 0}</span>
                    <span className="stat-label">Posts</span>
                  </div>
                </div>
              )}
            </div>

            {/* Recommended Section (Brands for Influencers, Influencers for Brands) */}
            {(user?.userType === 'Brand' || user?.userType === 'Influencer') && (
              <div className="reco-section">
                <div className="reco-header">
                  <h2 className="reco-title">
                    {user?.userType === 'Brand' ? 'Recommended Influencers' : 'Recommended Brands'}
                  </h2>
                  <button
                    className="cta-btn cta-btn--secondary"
                    style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                    onClick={() => onNavigate('owly')}
                  >
                    View all
                  </button>
                </div>

                <div className="reco-grid">
                  {recommendedInfluencers.map(inf => (
                    <div
                      key={inf.id}
                      className="influencer-card"
                      onClick={() => window.open(`https://www.instagram.com/${inf.handle.replace('@', '')}`, '_blank')}
                    >
                      <div className="influencer-profile">
                        <div className="influencer-avatar">
                          {inf.profile_pic ? (
                            <img src={inf.profile_pic} alt="avatar" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          ) : (
                            inf.name ? inf.name.charAt(0) : 'U'
                          )}
                        </div>
                        <div className="influencer-info">
                          <h4>{inf.name}</h4>
                          <span className="influencer-handle">{inf.handle}</span>
                        </div>
                        <div className="clout-badge">{inf.clout} Clout</div>
                      </div>

                      <div className="influencer-stats">
                        <div className="influencer-stat">
                          <span className="influencer-stat-value">{inf.followers}</span>
                          <span className="influencer-stat-label">Followers</span>
                        </div>
                        <div className="influencer-stat">
                          <span className="influencer-stat-value">{inf.niche}</span>
                          <span className="influencer-stat-label">Niche</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </main>

      {/* Edit Profile Modal */}
      {showEditProfile && (
        <EditProfileModal
          onClose={() => setShowEditProfile(false)}
          onSaved={(updatedUser) => setCurrentUserState(updatedUser)}
        />
      )}

      {/* User Profile Modal */}
      {viewProfileId && (
        <UserProfileModal
          userId={viewProfileId}
          onClose={() => setViewProfileId(null)}
          onMessageClick={() => handleMessageClick(viewProfileId)}
        />
      )}
    </div>
  );
};

export default MainPage;
