import React from 'react';

interface OwlIconProps {
  size?: number;
  className?: string;
}

const OwlIcon: React.FC<OwlIconProps> = ({ size = 48, className = '' }) => (
  <svg
    width={size}
    height={size}
    viewBox="0 0 100 110"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
  >
    <style>
      {`
        .owl-eyes {
          transform-origin: 50px 36px;
          animation: blink 5s infinite;
        }
        @keyframes blink {
          0%, 92%, 96%, 100% { transform: scaleY(1); }
          94%, 98% { transform: scaleY(0.1); }
        }
      `}
    </style>
    {/* Body */}
    <ellipse cx="50" cy="72" rx="32" ry="34" fill="#E8921A" />
    {/* Chest */}
    <ellipse cx="50" cy="80" rx="20" ry="22" fill="#F5B942" />
    {/* Head */}
    <circle cx="50" cy="38" r="32" fill="#E8921A" />
    {/* Ear tufts */}
    <polygon points="24,14 18,2 32,12" fill="#8B4513" />
    <polygon points="76,14 82,2 68,12" fill="#8B4513" />

    {/* Eyes */}
    <g className="owl-eyes">
      {/* Eye whites */}
      <circle cx="36" cy="36" r="13" fill="white" />
      <circle cx="64" cy="36" r="13" fill="white" />
      {/* Eye dark ring */}
      <circle cx="36" cy="36" r="10" fill="#3d1a00" />
      <circle cx="64" cy="36" r="10" fill="#3d1a00" />
      {/* Eye pupils */}
      <circle cx="36" cy="36" r="6" fill="#1a0a00" />
      <circle cx="64" cy="36" r="6" fill="#1a0a00" />
      {/* Eye glints */}
      <circle cx="39" cy="33" r="2.5" fill="white" />
      <circle cx="67" cy="33" r="2.5" fill="white" />
    </g>

    {/* Beak */}
    <polygon points="50,44 44,52 56,52" fill="#D4620A" />

    {/* Wings */}
    <g className="owl-wings">
      {/* Wing left */}
      <ellipse cx="22" cy="74" rx="10" ry="18" fill="#C97B10" transform="rotate(-15 22 74)" />
      {/* Wing right */}
      <ellipse cx="78" cy="74" rx="10" ry="18" fill="#C97B10" transform="rotate(15 78 74)" />
    </g>

    {/* Feet */}
    <ellipse cx="38" cy="104" rx="8" ry="4" fill="#C97B10" />
    <ellipse cx="62" cy="104" rx="8" ry="4" fill="#C97B10" />
  </svg>
);

export default OwlIcon;
