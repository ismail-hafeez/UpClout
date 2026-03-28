import React from 'react';

interface BellIconProps {
  size?: number;
  className?: string;
}

const BellIcon: React.FC<BellIconProps> = ({ size = 26, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    style={{ overflow: 'visible', filter: 'drop-shadow(0px 3px 5px rgba(29, 78, 216, 0.35))' }}
  >
    <defs>
      <linearGradient id="bellBlue" x1="2" y1="4" x2="22" y2="20" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stopColor="#60A5FA" />    {/* Light Blue */}
        <stop offset="45%" stopColor="#3B82F6" />   {/* Solid Blue */}
        <stop offset="100%" stopColor="#1D4ED8" />  {/* Dark Blue */}
      </linearGradient>
    </defs>
    
    <rect x="1.5" y="4" width="21" height="16" rx="3.5" fill="url(#bellBlue)" />
    
    <g transform="translate(3.6, 3.25) scale(0.7)" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </g>
  </svg>
);

export default BellIcon;
