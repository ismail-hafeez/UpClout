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
    style={{ overflow: 'visible' }}
  >
    {/* Transparent background — uses button background instead */}
    <path
      d="M11 5L12 14L9 20H13L15 14L21 9C21 9 18 5 11 5Z"
      stroke="white"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M11 5L10 14"
      stroke="white"
      strokeWidth="2.2"
      strokeLinecap="round"
    />
  </svg>
);

export default CampaignIcon;
