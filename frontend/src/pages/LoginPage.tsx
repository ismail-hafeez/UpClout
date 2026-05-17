import React, { useState, useEffect, useMemo } from 'react';
import { apiLogin, apiRegister, setToken, setCurrentUser, apiGetShowcaseWall } from '../services/api';
import './LoginPage.css';

interface LoginPageProps {
  onLogin: () => void;
  onBack: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin, onBack }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userType, setUserType] = useState('Influencer');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [profiles, setProfiles] = useState<any[]>([]);

  // Lock body scroll while on login page
  useEffect(() => {
    document.body.classList.add('login-page-active');
    return () => document.body.classList.remove('login-page-active');
  }, []);

  useEffect(() => {
    apiGetShowcaseWall().then(data => {
      // Get exactly 6 random profiles from the wall
      const shuffled = [...data].sort(() => 0.5 - Math.random());
      setProfiles(shuffled.slice(0, 6));
    });
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) { setError('Please fill in all fields.'); return; }
    if (isRegister && !email) { setError('Email is required to register.'); return; }

    setError('');
    setLoading(true);
    try {
      const data = isRegister
        ? await apiRegister({ username, email, password, userType })
        : await apiLogin({ username, password });

      setToken(data.token);
      setCurrentUser(data.user);
      onLogin();
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-root">
      {/* ===== LEFT PANE ===== */}
      <div className="login-left-pane">
        {/* Decorative blobs */}
        <div className="left-blob left-blob--1" />
        <div className="left-blob left-blob--2" />
        <div className="left-blob left-blob--3" />

        {/* Slogan */}
        <div className="left-content">
          <h1 className="left-slogan__heading">
            Redefining<br />
            Influencer<br />
            Marketing<br />
            <span className="left-slogan__accent">with AI</span>
          </h1>
          <p className="left-slogan__sub">
            Connect with the right creators. Zero searching required.
          </p>
        </div>

        {/* Floating Profile Cards */}
        <div className="left-cards-container">
          {profiles.map((profile, i) => (
            <div key={profile.username || i} className="profile-card">
              <img src={profile.profile_pic} alt={profile.name} className="profile-card-img" />
              <div className="profile-card-info">
                <span className="profile-card-name">{profile.name}</span>
                <span className="profile-card-niche">{profile.niche}</span>
                <span className={`profile-card-type ${profile.user_type?.toLowerCase()}`}>{profile.user_type}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ===== RIGHT PANE — Auth Form ===== */}
      <div className="login-right-pane">
        {/* Back button */}
        <button className="login-back-btn" onClick={onBack} aria-label="Go back to landing page">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
          </svg>
        </button>

        <div className="login-form-brand">
          <span className="brand-up">Up</span>
          <span className="brand-clout">Clout</span>
        </div>
        <h2 className="login-form-title">{isRegister ? 'Create account' : 'Welcome back'}</h2>
        <p className="login-form-subtitle">{isRegister ? 'Sign up to get started' : 'Sign in to your account'}</p>

        <div className="login-form-scroll-area">
          <form className="login-form" onSubmit={handleLogin}>
            <div className="form-group">
              <input
                className="form-input"
                type="text"
                placeholder="Instagram Username"
                value={username}
                onChange={e => setUsername(e.target.value)}
                autoComplete="username"
              />
            </div>

            {isRegister && (
              <>
                <div className="form-group">
                  <input
                    className="form-input"
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    autoComplete="email"
                  />
                </div>
                <div className="user-type-group">
                  <label className={`user-type-card ${userType === 'Influencer' ? 'user-type-card--selected' : ''}`}>
                    <input type="radio" name="userType" value="Influencer" checked={userType === 'Influencer'} onChange={() => setUserType('Influencer')} className="sr-only" />
                    <div className="user-type-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                        <circle cx="12" cy="7" r="4"></circle>
                      </svg>
                    </div>
                    <span>Influencer</span>
                  </label>
                  <label className={`user-type-card ${userType === 'Brand' ? 'user-type-card--selected' : ''}`}>
                    <input type="radio" name="userType" value="Brand" checked={userType === 'Brand'} onChange={() => setUserType('Brand')} className="sr-only" />
                    <div className="user-type-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                        <line x1="3" y1="9" x2="21" y2="9"></line>
                        <line x1="9" y1="21" x2="9" y2="9"></line>
                      </svg>
                    </div>
                    <span>Brand</span>
                  </label>
                </div>
              </>
            )}

            <div className="form-group">
              <div className="input-with-icon">
                <input
                  className="form-input"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="eye-toggle"
                  onClick={() => setShowPassword(v => !v)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94" />
                      <path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19" />
                      <line x1="1" y1="1" x2="23" y2="23" />
                    </svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
                      <circle cx="12" cy="12" r="3" />
                    </svg>
                  )}
                </button>
              </div>
            </div>

            {error && <div className="form-error">{error}</div>}

            <button
              type="submit"
              className={`login-btn ${loading ? 'login-btn--loading' : ''}`}
              disabled={loading}
            >
              {loading ? (
                <span className="spinner" />
              ) : isRegister ? 'REGISTER' : 'LOGIN'}
            </button>
          </form>
        </div>

        <p className="register-link">
          {isRegister ? 'Already have an account? ' : "Don't have an account? "}
          <button
            type="button"
            className="register-btn"
            onClick={() => { setIsRegister(v => !v); setError(''); }}
          >
            {isRegister ? 'Login' : 'Register here'}
          </button>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;