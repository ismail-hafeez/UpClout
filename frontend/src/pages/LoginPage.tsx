import React, { useState } from 'react';
import { apiLogin, apiRegister, setToken, setCurrentUser } from '../services/api';
import './LoginPage.css';

interface LoginPageProps {
  onLogin: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [userType, setUserType] = useState('Influencer');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

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
      {/* Left hero panel */}
      <div className="login-hero">
        <div className="login-hero__brand"></div>
        <div className="login-hero__content">
          <h1 className="login-hero__heading">
            <span className="hero-word hero-word--1">Redefining</span>
            <span className="hero-word hero-word--2">Influencer</span>
            <span className="hero-word hero-word--3">Marketing <span className="hero-word--light">with</span></span>
            <span className="hero-word hero-word--4">AI</span>
          </h1>
          <p className="login-hero__sub">Connect with the right creators. Zero searching required.</p>
        </div>
        <div className="login-hero__decor">
          <div className="hero-circle hero-circle--1" />
          <div className="hero-circle hero-circle--2" />
          <div className="hero-circle hero-circle--3" />
        </div>
      </div>

      {/* Right form panel */}
      <div className="login-panel">
        <div className="login-form-container">
          <div className="login-form-brand">
            <span className="brand-up">Up</span>
            <span className="brand-clout">Clout</span>
          </div>
          <h2 className="login-form-title">{isRegister ? 'Create account' : 'Welcome back'}</h2>
          <p className="login-form-subtitle">{isRegister ? 'Sign up to get started' : 'Sign in to your account'}</p>

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

            <div className="captcha-row" style={{ justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              {!isRegister && (
                <button type="button" className="forgot-btn">Forgot password?</button>
              )}
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