import React from 'react';

interface CampaignIconProps {
  size?: number;
  className?: string;
}

const CampaignIcon: React.FC<CampaignIconProps> = ({ size = 26, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={{ overflow: 'visible', filter: 'drop-shadow(0px 3px 6px rgba(139, 92, 246, 0.4))' }}
  >
    <defs>
      <linearGradient id="campaignGrad" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stopColor="#A78BFA" />    {/* Light Purple */}
        <stop offset="50%" stopColor="#8B5CF6" />   {/* Solid Purple */}
        <stop offset="100%" stopColor="#6D28D9" />  {/* Dark Purple */}
      </linearGradient>
      <linearGradient id="accentGrad" x1="12" y1="12" x2="22" y2="22" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stopColor="#F472B6" />    {/* Pink */}
        <stop offset="100%" stopColor="#DB2777" />   {/* Dark Pink */}
      </linearGradient>
    </defs>

    {/* Megaphone Body */}
    <path
      d="M11.5 5.5C11.5 5.5 5 6.5 4 10.5C3 14.5 9.5 15.5 9.5 15.5L10.5 20.5H13.5L12.5 15.5C12.5 15.5 19 14.5 20 10.5C21 6.5 14.5 5.5 14.5 5.5H11.5Z"
      fill="url(#campaignGrad)"
    />

    {/* Front Ring / Outlet */}
    <ellipse
      cx="17.5"
      cy="10.5"
      rx="2"
      ry="4.5"
      fill="url(#accentGrad)"
    />

    {/* Handle / Detail */}
    <path
      d="M9 15.5L8 19.5"
      stroke="white"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
    
    {/* Sound Waves / Sparkle */}
    <path
      d="M21 7L23 5M21 14L23 16"
      stroke="#F472B6"
      strokeWidth="2"
      strokeLinecap="round"
    />
  </svg>
);

export default CampaignIcon;
