import React from 'react';

const statusTextColor = {
  RESOLVED:              '#1E8E5A',
  APPROVED:              '#1E8E5A',
  ACTIVE:                '#1E8E5A',
  ON_TRACK:              '#1E8E5A',
  COMPLETED:             '#1E8E5A',
  
  PENDING:               '#B98900',
  DELAYED:               '#B98900',
  IN_PROGRESS:           '#B98900',
  ANALYZING:             '#B98900',
  REPLANNING:            '#B98900',
  
  CRITICAL:              '#C4302B',
  REJECTED:              '#C4302B',
  SHUTDOWN_RISK:         '#C4302B',
  EMERGENCY_PROCUREMENT: '#C4302B',

  OPEN:                  '#3A4149',
  PROPOSED:              '#3A4149',
  CLOSED:                '#8A919B',
  INACTIVE:              '#8A919B',
  MONITORING:            '#3A4149',
};

export default function StatusBadge({ status }) {
  const textColor = statusTextColor[status] || '#3A4149';
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        fontSize: 12,
        fontWeight: 600,
        color: textColor,
        background: 'transparent',
        border: 'none',
        padding: 0,
        fontFamily: 'var(--font-mono)',
      }}
    >
      <span style={{ color: '#8A919B', fontSize: 10 }}>●</span>
      {status?.replace(/_/g, ' ')}
    </span>
  );
}
