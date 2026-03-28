import React from 'react';

interface MessageIconProps {
  size?: number;
  className?: string;
}

const MessageIcon: React.FC<MessageIconProps> = ({ size = 26, className = '' }) => (
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
      <linearGradient id="msgBlue" x1="2" y1="4" x2="22" y2="20" gradientUnits="userSpaceOnUse">
        <stop offset="0%" stopColor="#60A5FA" />    {/* Light Blue */}
        <stop offset="45%" stopColor="#3B82F6" />   {/* Solid Blue */}
        <stop offset="100%" stopColor="#1D4ED8" />  {/* Dark Blue */}
      </linearGradient>
    </defs>
    
    <rect x="1.5" y="4" width="21" height="16" rx="3.5" fill="url(#msgBlue)" />
    
    <path 
      d="M2.5 5.8L10.5 12.1C11.4 12.8 12.6 12.8 13.5 12.1L21.5 5.8" 
      stroke="white" 
      strokeWidth="2.2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
    />
  </svg>
);

export default MessageIcon;

