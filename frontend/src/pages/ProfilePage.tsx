import React, { useState, useEffect } from 'react';
import AnalyticsCharts from '../components/AnalyticsCharts';
import OwlIcon from '../components/OwlIcon';
import { apiGetProfileDetails, apiGetAnalytics, getAvatarUrl } from '../services/api';
import './ProfilePage.css';

interface ProfilePageProps {
  username: string;
  onNavigate: (page: string, params?: any) => void;
  onBack: () => void;
}

const ProfilePage: React.FC<ProfilePageProps> = ({ username, onNavigate, onBack }) => {
  const [profile, setProfile] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [profileRes, analyticsRes] = await Promise.all([
          apiGetProfileDetails(username),
          apiGetAnalytics(username)
        ]);
        setProfile(profileRes);
        setAnalytics(analyticsRes);
      } catch (err) {
        console.error('Fetch Profile Error:', err);
        setError('Could not load profile details. They might not be in our database yet.');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [username]);

  if (loading) {
    return (
      <div className="profile-loading">
        <div className="loader"></div>
        <p>Fetching @{username}'s details...</p>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="profile-error">
        <h3>Oops!</h3>
        <p>{error || 'Profile not found.'}</p>
        <button className="cta-btn" onClick={onBack}>Go Back</button>
      </div>
    );
  }

  return (
    <div className="profile-root">
      {/* Background container */}
      <div className="profile-bg-shapes"></div>

      {/* Header / Nav */}
      <div className="profile-nav">
        <button className="back-link" onClick={onBack}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
          </svg>
          Back to Search
        </button>
      </div>

      <div className="profile-content">
        {/* TOP SECTION: Identity & Stats */}
        <section className="profile-identity-section glass">
          <div className="identity-left">
            <div className="profile-avatar-large">
              <img src={profile.profile_pic || `https://api.dicebear.com/7.x/thumbs/svg?seed=${username}`} alt={profile.username} />
            </div>
            <div className="identity-text">
              <h1 className="profile-name">{profile.name}</h1>
              <div className="profile-handle-row">
                <span className="profile-handle">@{profile.username}</span>
                <span className="profile-badge">{profile.type}</span>
              </div>
              <p className="profile-bio">{profile.bio}</p>
              <div className="profile-meta">
                <span>📍 {profile.location}</span>
                <span>🏷️ {profile.niche}</span>
              </div>
            </div>
          </div>
          
          <div className="identity-right-stats">
            <div className="stat-box">
              <span className="stat-val">{profile.followers?.toLocaleString()}</span>
              <span className="stat-lab">Followers</span>
            </div>
            <div className="stat-box">
              <span className="stat-val">{profile.eng_rate}%</span>
              <span className="stat-lab">Eng. Rate</span>
            </div>
            <div className="stat-box">
              <span className="stat-val">{profile.posts?.toLocaleString()}</span>
              <span className="stat-lab">Total Posts</span>
            </div>
          </div>
        </section>

        <div className="profile-secondary-grid">
          {/* OWLY SUMMARY */}
          <section className="owly-summary-card glass">
            <div className="owly-summary-header">
              <div className="owly-avatar-mini">
                <OwlIcon size={32} />
              </div>
              <h3>Owly's Take</h3>
            </div>
            <p className="summary-text">{profile.summary}</p>
          </section>

          {/* TOP POST */}
          {profile.top_post && (
            <section className="top-post-card glass">
              <div className="top-post-header">
                <span className="crown-icon">👑</span>
                <h3>Highest Liked Post</h3>
              </div>
              <div className="top-post-preview">
                {profile.top_post.type === 'Video' || profile.top_post.type === 'Reel' ? (
                  <div className="video-placeholder">🎥 Video Content</div>
                ) : (
                  <img src={profile.top_post.url} alt="Top post" className="top-post-img" />
                )}
                <div className="top-post-overlay">
                  <div className="overlay-stat">❤️ {profile.top_post.likes?.toLocaleString()}</div>
                  <div className="overlay-stat">💬 {profile.top_post.comments?.toLocaleString()}</div>
                </div>
              </div>
              <p className="top-post-caption">{profile.top_post.caption?.substring(0, 80)}...</p>
              <span className="top-post-date">{profile.top_post.date}</span>
            </section>
          )}
        </div>

        {/* ANALYTICS SECTION */}
        <section className="profile-analytics-section" style={{ padding: '2.5rem' }}>
          <h2 className="section-title" style={{ marginTop: 0 }}>Visual <span className="accent">Analytics</span></h2>
          <AnalyticsCharts data={analytics} />
        </section>

        {/* FOOTER CTA */}
        <div className="profile-footer" style={{ flexWrap: 'wrap' }}>
          <button 
            className="cta-btn cta-btn--primary" 
            onClick={() => window.open(`https://www.instagram.com/${username.replace('@', '')}`, '_blank')}
          >
            Visit Instagram Profile
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginLeft: '8px' }}>
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" /><polyline points="15 3 21 3 21 9" /><line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </button>

          {profile.mongo_id && (
            <button 
              className="cta-btn cta-btn--secondary"
              onClick={() => {
                localStorage.setItem('openChatUserId', profile.mongo_id);
                onNavigate('chats');
              }}
              style={{ padding: '0.8rem 1.5rem' }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '8px' }}>
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              Message
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;
