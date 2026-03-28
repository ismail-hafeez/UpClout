import React, { useState } from 'react';

interface StarRatingProps {
  value: number; // Can be fractional (e.g., 4.2)
  onChange?: (val: number) => void;
  readOnly?: boolean;
  size?: number;
}

const StarRating: React.FC<StarRatingProps> = ({ value, onChange, readOnly = false, size = 22 }) => {
  const [hoverValue, setHoverValue] = useState<number | null>(null);
  // Generate a unique ID per instance to avoid SVG def collision across the DOM
  const [componentId] = useState(() => Math.random().toString(36).substring(2, 9));

  const handlePointerMove = (e: React.MouseEvent<SVGSVGElement>, index: number) => {
    if (readOnly) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const isHalf = x < rect.width / 2;
    setHoverValue(isHalf ? index + 0.5 : index + 1);
  };

  const currentVal = hoverValue !== null ? hoverValue : value;

  const renderStar = (index: number) => {
    let fillPercentage = 0;
    if (currentVal >= index + 1) fillPercentage = 1;
    else if (currentVal > index) fillPercentage = currentVal - index;

    const gradId = `starGrad-${componentId}-${index}`;
    const clipId = `starClip-${componentId}-${index}`;

    return (
      <svg
        key={index}
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          flexShrink: 0,
          cursor: readOnly ? 'default' : 'pointer',
          transition: 'transform 0.15s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
          transform: (hoverValue && hoverValue > index && hoverValue <= index + 1 && !readOnly) ? 'scale(1.15)' : 'scale(1)',
          filter: fillPercentage > 0.5 ? 'drop-shadow(0px 2px 4px rgba(234, 179, 8, 0.3))' : 'none',
        }}
        onMouseMove={e => handlePointerMove(e, index)}
        onMouseLeave={() => !readOnly && setHoverValue(null)}
        onClick={() => !readOnly && onChange && hoverValue && onChange(hoverValue)}
      >
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="24" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#FEF08A" />    {/* Light Yellow */}
            <stop offset="30%" stopColor="#FFD700" />   {/* Bright Gold */}
            <stop offset="100%" stopColor="#D97706" />  {/* Deep Gold */}
          </linearGradient>
          <clipPath id={clipId}>
            <rect x="0" y="0" width={fillPercentage * 24} height="24" />
          </clipPath>
        </defs>
        
        {/* Empty Star Background */}
        <path
          d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
          fill="#E2E8F0"
        />

        {/* Filled Star Foreground (Clipped for fractional rating) */}
        {fillPercentage > 0 && (
          <path
            d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
            fill={`url(#${gradId})`}
            clipPath={`url(#${clipId})`}
          />
        )}
      </svg>
    );
  };

  return (
    <div style={{ display: 'inline-flex', gap: '0.15rem', alignItems: 'center', flexShrink: 0 }} onMouseLeave={() => !readOnly && setHoverValue(null)}>
      {[...Array(5)].map((_, i) => renderStar(i))}
    </div>
  );
};

export default StarRating;
