import React from 'react';

const severityTextColor = {
  CRITICAL: '#C4302B',
  HIGH:     '#C4302B',
  MEDIUM:   '#B98900',
  LOW:      '#1E8E5A',
  NONE:     '#8A919B',
  UNKNOWN:  '#8A919B',
};

export default function RiskBadge({ level }) {
  const textColor = severityTextColor[level] || '#8A919B';
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        fontSize: 12,
        fontWeight: 700,
        color: textColor,
        background: 'transparent',
        border: 'none',
        padding: 0,
        fontFamily: 'var(--font-mono)',
        letterSpacing: 0.3,
      }}
    >
      <span style={{ color: '#8A919B', fontSize: 10 }}>●</span>
      {level}
    </span>
  );
}
