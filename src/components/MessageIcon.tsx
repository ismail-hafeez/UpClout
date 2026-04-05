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
    style={{ overflow: 'visible' }}
  >
    {/* Transparent background — uses button background instead */}
    <rect 
      x="3" 
      y="5" 
      width="18" 
      height="14" 
      rx="2" 
      stroke="white" 
      strokeWidth="2.2" 
    />
    <path 
      d="M3 7L12 13L21 7" 
      stroke="white" 
      strokeWidth="2.2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
    />
  </svg>
);

export default MessageIcon;
