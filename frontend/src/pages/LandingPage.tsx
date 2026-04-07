import React, { useState, useEffect, useRef } from 'react';
import OwlIcon from '../components/OwlIcon';
import './LandingPage.css';

interface LandingPageProps {
  onTryNow: () => void;
}

const LandingPage: React.FC<LandingPageProps> = ({ onTryNow }) => {
  // ---- Smart navbar ----
  const [navHidden, setNavHidden] = useState(false);
  const [navScrolled, setNavScrolled] = useState(false);
  const lastScrollY = useRef(0);

  useEffect(() => {
    const handleScroll = () => {
      const currentY = window.scrollY;
      setNavScrolled(currentY > 60);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // ---- Section reveal on scroll ----
  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('lp-reveal--visible');
          }
        });
      },
      { threshold: 0.15 }
    );
    document.querySelectorAll('.lp-reveal').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  // ---- Smooth scroll to section ----
  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  // ---- Particles ----
  const particles = Array.from({ length: 30 }, (_, i) => {
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
    <div className="landing-root">
      {/* Dynamic Background Shapes */}
      <div className="lp-bg-shapes">
        <div className="shape shape-1"></div>
        <div className="shape shape-2"></div>
        <div className="shape shape-3"></div>
      </div>

      {/* Floating particles */}
      <div className="lp-particles">{particles}</div>

      {/* ===== NAV ===== */}
      <nav className={`lp-nav${navScrolled ? ' lp-nav--scrolled' : ''}`}>
        <div className="lp-nav-brand">
          <span className="lp-brand-up">Up</span>
          <span className="lp-brand-clout">Clout</span>
        </div>
        <div className="lp-nav-links">
          <button className="lp-nav-link" onClick={() => scrollTo('owly')}>Owly</button>
          <button className="lp-nav-link" onClick={() => scrollTo('features')}>Features</button>
          <button className="lp-nav-try" onClick={onTryNow}>
            Get Started →
          </button>
        </div>
      </nav>

      {/* ===== HERO ===== */}
      <section className="lp-hero" id="hero">
        <h1 className="lp-hero-title">
          Everyone has <span className="lp-hero-title-accent">clout</span>
          <br />
          Discover yours.
        </h1>

        <p className="lp-hero-sub">
          Find the perfect influencer for your brand.<br />
          Let us do the searching while you focus on creating.
        </p>

        <div className="lp-hero-cta-group">
          <button className="lp-cta-primary" onClick={onTryNow}>
            Try UpClout Free &rarr;
          </button>
          <button className="lp-cta-secondary" onClick={() => scrollTo('owly')}>
            Meet Owly
          </button>
        </div>

        {/* Glass stats card */}
        <div className="lp-hero-visual">
          <div className="lp-glass-card">
            <div className="lp-glass-stat">
              <div className="lp-glass-stat-number">50K+</div>
              <div className="lp-glass-stat-label">Creators</div>
            </div>
            <div className="lp-glass-divider" />
            <div className="lp-glass-stat">
              <div className="lp-glass-stat-number">2.4K</div>
              <div className="lp-glass-stat-label">Brands</div>
            </div>
            <div className="lp-glass-divider" />
            <div className="lp-glass-stat">
              <div className="lp-glass-stat-number">6.4%</div>
              <div className="lp-glass-stat-label">Avg. Engagement</div>
            </div>
          </div>
        </div>

      </section>

      {/* ===== OWLY SECTION ===== */}
      <section className="lp-owly" id="owly">
        <div className="lp-owly-inner lp-reveal">
          <div className="lp-owly-visual">
            <div className="lp-owly-glow" />
            <div className="lp-owly-icon-wrap">
              <OwlIcon size={180} />
            </div>
          </div>
          <div className="lp-owly-content">
            <span className="lp-owly-tag">AI ASSISTANT</span>
            <h2 className="lp-owly-title">
              Meet <span className="lp-owly-title-accent">Owly</span>
              <br />
              Your helpful AI assistant
            </h2>
            <p className="lp-owly-desc">
              Describe your campaign goals and Owly instantly finds the perfect influencer
              matches. No more endless scrolling — just results.
            </p>
            <div className="lp-owly-features">
              <div className="lp-owly-feature">
                <span className="lp-owly-feature-dot" />
                AI-powered niche &amp; audience analysis
              </div>
              <div className="lp-owly-feature">
                <span className="lp-owly-feature-dot" />
                Smart matching based on engagement, not just followers
              </div>
              <div className="lp-owly-feature">
                <span className="lp-owly-feature-dot" />
                Connect directly — no middlemen, no delays
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== CATEGORIES SECTION ===== */}
      <section className="lp-categories" id="prowess">
        <div className="lp-categories-header lp-reveal">
          <span className="lp-categories-tag">DIVERSITY</span>
          <h2 className="lp-categories-title">
            Our Market <span className="lp-categories-title-accent">Prowess</span>
          </h2>
          <p className="lp-categories-subtitle">
            Dominating the landscape across multiple high-impact niches.
          </p>
        </div>

        <div className="lp-categories-content lp-reveal">
          {/* Brand Prowess */}
          <div className="lp-prowess-col">
            <h3 className="lp-prowess-col-title">Top Brand Sectors</h3>
            <div className="lp-prowess-items">
              {[
                { name: 'Fashion & Accessories', pct: 32, icon: 'M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z' },
                { name: 'Tech & Software', pct: 24, icon: 'M16 18l6-6-6-6M8 6l-6 6 6 6' },
                { name: 'Health & Wellness', pct: 18, icon: 'M22 12h-4l-3 9L9 3l-3 9H2' },
                { name: 'Food & Beverage', pct: 14, icon: 'M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8z M6 1v3 M10 1v3 M14 1v3' },
                { name: 'Home & Lifestyle', pct: 12, icon: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10' },
              ].map((c) => (
                <div key={c.name} className="lp-prowess-item">
                  <div className="lp-prowess-info">
                    <div className="lp-prowess-icon-label">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d={c.icon} />
                      </svg>
                      <span>{c.name}</span>
                    </div>
                    <span className="lp-prowess-percentage">{c.pct}%</span>
                  </div>
                  <div className="lp-prowess-bar-bg">
                    <div className="lp-prowess-bar-fill lp-prowess-bar--blue" style={{ width: `${c.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="lp-prowess-divider-v" />

          {/* Influencer Prowess */}
          <div className="lp-prowess-col">
            <h3 className="lp-prowess-col-title">Top Creator Niches</h3>
            <div className="lp-prowess-items">
              {[
                { name: 'Lifestyle & Travel', pct: 35, icon: 'M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z M12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6z' },
                { name: 'Gaming & Tech', pct: 22, icon: 'M6 12h4M8 10v4M15 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2z M18 11a1 1 0 1 0 0-2 1 1 0 0 0 0 2z M21 7v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z' },
                { name: 'Beauty & Fashion', pct: 18, icon: 'M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z M12 17a4 4 0 1 0 0-8 4 4 0 0 0 0 8z' },
                { name: 'Fitness & Sports', pct: 15, icon: 'M6.7 6.7l10.6 10.6M6.7 17.3L17.3 6.7M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z' },
                { name: 'Education & Finance', pct: 10, icon: 'M12 1v22M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6' },
              ].map((c) => (
                <div key={c.name} className="lp-prowess-item">
                  <div className="lp-prowess-info">
                    <div className="lp-prowess-icon-label">
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d={c.icon} />
                      </svg>
                      <span>{c.name}</span>
                    </div>
                    <span className="lp-prowess-percentage">{c.pct}%</span>
                  </div>
                  <div className="lp-prowess-bar-bg">
                    <div className="lp-prowess-bar-fill lp-prowess-bar--purple" style={{ width: `${c.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ===== FEATURES SECTION ===== */}
      <section className="lp-features" id="features">
        <div className="lp-features-header lp-reveal">
          <span className="lp-features-tag">PLATFORM</span>
          <h2 className="lp-features-title">
            Everything you need to{' '}
            <span className="lp-features-title-accent">scale</span>
          </h2>
          <p className="lp-features-subtitle">
            From discovery to payment — UpClout handles the entire influencer
            marketing lifecycle in one place.
          </p>
        </div>

        <div className="lp-features-grid lp-reveal">
          <div className="lp-feature-card">
            <div className="lp-feature-icon lp-feature-icon--blue">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#60a5fa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
              </svg>
            </div>
            <h3>Smart Discovery</h3>
            <p>Find creators that match your brand's audience, niche, and budget with AI precision.</p>
          </div>

          <div className="lp-feature-card">
            <div className="lp-feature-icon lp-feature-icon--purple">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <h3>Real-time Chat</h3>
            <p>Message creators directly, share files, and negotiate — all within one platform.</p>
          </div>

          <div className="lp-feature-card">
            <div className="lp-feature-icon lp-feature-icon--teal">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18" /><path d="M9 21V9" />
              </svg>
            </div>
            <h3>Campaign Management</h3>
            <p>Track deliverables, manage budgets, and monitor progress from a single dashboard.</p>
          </div>
        </div>
        <div className="lp-bottom-cta lp-reveal">
          <button className="lp-cta-primary" onClick={onTryNow}>
            Start For Free
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
            </svg>
          </button>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="lp-footer">
        <div className="lp-footer-brand">
          <span className="lp-brand-up">Up</span>
          <span className="lp-brand-clout">Clout</span>
        </div>
        <p className="lp-footer-copy">
          © 2026 UpClout. All rights reserved.
          <br />
          Redefining influencer marketing with AI.
        </p>
        <div className="lp-footer-links">
          <button className="lp-footer-link">Privacy Policy</button>
          <button className="lp-footer-link">Terms of Service</button>
          <button className="lp-footer-link" onClick={onTryNow}>Sign In</button>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
