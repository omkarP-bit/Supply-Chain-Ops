import React from 'react';

const statusColors = {
  OPEN:              { bg: '#e3f2fd', text: '#1565c0' },
  IN_PROGRESS:       { bg: '#fff3e0', text: '#e65100' },
  RESOLVED:          { bg: '#e8f5e9', text: '#2e7d32' },
  CLOSED:            { bg: '#f5f5f5', text: '#616161' },
  PENDING:           { bg: '#fff8e1', text: '#f57f17' },
  APPROVED:          { bg: '#e8f5e9', text: '#2e7d32' },
  REJECTED:          { bg: '#ffebee', text: '#c62828' },
  PROPOSED:          { bg: '#e3f2fd', text: '#1565c0' },
  ACTIVE:            { bg: '#e8f5e9', text: '#2e7d32' },
  INACTIVE:          { bg: '#f5f5f5', text: '#616161' },
  DELAYED:           { bg: '#ffebee', text: '#c62828' },
  ON_TRACK:          { bg: '#e8f5e9', text: '#2e7d32' },
  EMERGENCY_PROCUREMENT: { bg: '#ffebee', text: '#c62828' },
  PRODUCTION_ADJUSTMENT: { bg: '#fff3e0', text: '#e65100' },
  MONITORING:        { bg: '#e3f2fd', text: '#1565c0' },
};

export default function StatusBadge({ status }) {
  const c = statusColors[status] || { bg: '#f5f5f5', text: '#616161' };
  return (
    <span style={{
      display: 'inline-block',
      padding: '3px 10px',
      borderRadius: 12,
      fontSize: 12,
      fontWeight: 600,
      background: c.bg,
      color: c.text,
    }}>
      {status?.replace(/_/g, ' ')}
    </span>
  );
}
