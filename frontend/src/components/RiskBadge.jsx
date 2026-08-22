import React from 'react';

const colors = {
  CRITICAL: { bg: '#ffebee', text: '#c62828', border: '#ef9a9a' },
  HIGH:     { bg: '#fff3e0', text: '#e65100', border: '#ffcc80' },
  MEDIUM:   { bg: '#fff8e1', text: '#f57f17', border: '#ffe082' },
  LOW:      { bg: '#e8f5e9', text: '#2e7d32', border: '#a5d6a7' },
  NONE:     { bg: '#f5f5f5', text: '#757575', border: '#e0e0e0' },
  UNKNOWN:  { bg: '#f5f5f5', text: '#757575', border: '#e0e0e0' },
};

export default function RiskBadge({ level }) {
  const c = colors[level] || colors.UNKNOWN;
  return (
    <span style={{
      display: 'inline-block',
      padding: '3px 10px',
      borderRadius: 12,
      fontSize: 12,
      fontWeight: 700,
      letterSpacing: 0.5,
      background: c.bg,
      color: c.text,
      border: `1px solid ${c.border}`,
    }}>
      {level}
    </span>
  );
}
