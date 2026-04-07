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
    style={{ overflow: 'visible' }}
  >
    {/* No internal background circle — uses button background instead */}
    <g transform="translate(4.8, 4.8) scale(0.6)" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round" strokeLinejoin="round">
      <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
      <path d="M13.73 21a2 2 0 0 1-3.46 0" />
    </g>
  </svg>
);

export default BellIcon;
