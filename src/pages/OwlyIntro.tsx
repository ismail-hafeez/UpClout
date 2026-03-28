import React from 'react';
import OwlIcon from '../components/OwlIcon';
import './OwlyIntro.css';

interface OwlyIntroProps {
  onContinue: () => void;
  onBack: () => void;
}

const OwlyIntro: React.FC<OwlyIntroProps> = ({ onContinue, onBack }) => {
  return (
    <div className="owly-intro-root">
      <div className="owly-intro-nav">
        <button className="back-btn" onClick={onBack} aria-label="Go back">
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="15 18 9 12 15 6"/>
  </svg>
</button>
        <div className="nav-brand owly-nav-brand">
          <span className="brand-up">Up</span>
          <span className="brand-clout">Clout</span>
        </div>
      </div>

      <div className="owly-intro-stage">
        <div className="owly-intro-card">
          {/* Left content */}
          <div className="owly-intro-text">
            
            <h1 className="owly-intro-name">Meet Owly</h1>
            <h2 className="owly-intro-tagline">Your helpful AI assistant</h2>
            <p className="owly-intro-slogan">
              <em>Right influencer. Zero searching</em>
            </p>

            <ul className="owly-features">
              <li className="owly-feature-item">
                <span className="owly-feature-dot" />
                Describe your campaign and Owly finds matches
              </li>
              <li className="owly-feature-item">
                <span className="owly-feature-dot" />
                AI-powered niche &amp; audience analysis
              </li>
              <li className="owly-feature-item">
                <span className="owly-feature-dot" />
                Connect directly, no middlemen
              </li>
            </ul>

            <button className="owly-cta" onClick={onContinue}>
              <span>Start chatting with Owly</span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"/>
                <polyline points="12 5 19 12 12 19"/>
              </svg>
            </button>
          </div>

          {/* Right owl mascot */}
          <div className="owly-mascot-area">
            <div className="owly-mascot-bg" />
            <div className="owly-mascot-wrapper">
              <OwlIcon size={180} className="owly-mascot-icon" />
              <div className="owly-speech-bubble">
                <span>Hi! Let me find your perfect influencer 👋</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OwlyIntro;
