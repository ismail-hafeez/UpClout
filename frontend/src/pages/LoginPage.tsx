import React, { useState, useEffect, useMemo } from 'react';
import { apiLogin, apiRegister, setToken, setCurrentUser, apiGetShowcaseWall } from '../services/api';
import './LoginPage.css';

interface LoginPageProps {
  onLogin: () => void;
  onBack: () => void;
  initialProfiles?: ShowcaseProfile[];
}

interface ShowcaseProfile {
  name: string;
  username: string;
  profile_pic: string;
  niche: string;
  followers: number;
  user_type: string;
}

const NUM_COLUMNS = 20;

const LoginPage: React.FC<LoginPageProps> = ({ onLogin, onBack, initialProfiles = [] }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userType, setUserType] = useState('Influencer');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [profiles, setProfiles] = useState<ShowcaseProfile[]>(initialProfiles);

  // Fetch showcase profiles only if they weren't passed in (fallback)
  useEffect(() => {
    if (profiles.length === 0) {
      apiGetShowcaseWall()
        .then((data: ShowcaseProfile[]) => {
          if (data && data.length > 0) setProfiles(data);
        })
        .catch(() => {});
    }
  }, [profiles.length]);

  // Lock body scroll while on login page
  useEffect(() => {
    document.body.classList.add('login-page-active');
    return () => document.body.classList.remove('login-page-active');
  }, []);

  // Distribute profiles across columns (duplicate for seamless loop)
  const columns = useMemo(() => {
    if (profiles.length === 0) return [];
    
    // Shuffle the profiles first for more variety
    const shuffled = [...profiles].sort(() => Math.random() - 0.5);
    
    const cols: ShowcaseProfile[][] = Array.from({ length: NUM_COLUMNS }, () => []);
    // Distribute profiles round-robin
    shuffled.forEach((p, i) => {
      cols[i % NUM_COLUMNS].push(p);
    });
    // Duplicate each column 8x for a lot of scrolling room before reset
    return cols.map(col => {
      return Array(8).fill(col).flat();
    });
  }, [profiles]);

  // Particles logic from LandingPage to match theme
  const particles = useMemo(() => {
    return Array.from({ length: 20 }, (_, i) => {
      const left = Math.random() * 100;
      const size = 2 + Math.random() * 3;
      const dur = 8 + Math.random() * 14;
      const delay = Math.random() * 10;
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
            background: 'rgba(37, 99, 235, 0.15)',
          }}
        />
      );
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

  // Column animation speeds (different for parallax effect)
  const columnSpeeds = [28, 22, 32, 20, 30, 24, 26, 34, 21, 29, 23, 31, 27, 25, 33, 26, 30, 22, 24, 28];

  // Helper to format large numbers
  const formatNumber = (num: number) => {
    if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
    if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
    return num.toString();
  };

  return (
    <div className="login-root">
      {/* Background Shapes from LandingPage */}
      <div className="lp-bg-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
      </div>

      {/* Floating particles from LandingPage */}
      <div className="login-particles">{particles}</div>

      {/* ===== FLOATING CARD WALL ===== */}
      <div className="card-wall">
        <div className="card-wall__inner">
          {columns.map((col, colIdx) => (
            <div
              key={colIdx}
              className="card-column"
              style={{
                animationDuration: `${columnSpeeds[colIdx % columnSpeeds.length]}s`,
              }}
            >
              {col.map((profile, cardIdx) => (
                <div key={`${colIdx}-${cardIdx}`} className="profile-card">
                  <div className="profile-card__img-wrap">
                    <img
                      src={profile.profile_pic}
                      alt={profile.name}
                      className="profile-card__img"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src =
                          `https://ui-avatars.com/api/?name=${encodeURIComponent(profile.name)}&background=1a3a8a&color=fff&size=120`;
                      }}
                    />
                  </div>
                  <div className="profile-card__info">
                    <span className="profile-card__name">{profile.name}</span>
                    <span className="profile-card__followers">{formatNumber(profile.followers)}</span>
                    <span className={`profile-card__niche ${profile.user_type === 'Brand' ? 'profile-card__niche--brand' : ''}`}>{profile.niche}</span>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* ===== DARK VIGNETTE OVERLAY ===== */}
      <div className="login-vignette" />

      {/* ===== GLASS AUTH FORM ===== */}
      <div className="login-glass-wrapper">
        <div className="login-glass">
          {/* ===== BACK BUTTON (Inside Form) ===== */}
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

              {/* Remvoed Forgot Password row */}

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
    </div>
  );
};

export default LoginPage;