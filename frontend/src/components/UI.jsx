import React from 'react';

export function Spinner({ size = 'md' }) {
  const s = size === 'sm' ? 14 : size === 'lg' ? 28 : 20;
  return (
    <div
      style={{
        display: 'inline-block',
        width: s,
        height: s,
        border: '2px solid rgba(255,255,255,0.3)',
        borderTopColor: '#fff',
        borderRadius: '50%',
        animation: 'spin 0.6s linear infinite',
      }}
    />
  );
}

export function Loading() {
  return (
    <div style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>
      Loading operational data...
    </div>
  );
}

export function Error({ message }) {
  return (
    <div style={{ padding: 20, background: '#fee2e2', borderRadius: 8, color: '#991b1b', border: '1px solid #fecaca' }}>
      {message || 'Something went wrong'}
    </div>
  );
}

export function Card({ children, style = {} }) {
  return (
    <div style={{
      background: '#fff',
      borderRadius: 10,
      padding: 20,
      boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      border: '1px solid #e2e8f0',
      ...style,
    }}>
      {children}
    </div>
  );
}

export function StatCard({ label, value, color }) {
  return (
    <Card style={{ textAlign: 'center', minWidth: 140 }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: color || '#1e293b' }}>{value}</div>
      <div style={{ fontSize: 13, color: '#64748b', marginTop: 4 }}>{label}</div>
    </Card>
  );
}

export function Button({ children, onClick, disabled = false, style = {} }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 6,
        padding: '8px 16px',
        background: '#0f172a',
        color: '#fff',
        border: 'none',
        borderRadius: 6,
        fontSize: 13,
        fontWeight: 600,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.7 : 1,
        transition: 'background 0.15s',
        ...style,
      }}
    >
      {children}
    </button>
  );
}

export function Table({ children, columns, rows, onRowClick }) {
  if (columns && rows) {
    return (
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
          <thead>
            <tr>
              {columns.map((col) => (
                <th key={col.key} style={{
                  textAlign: 'left',
                  padding: '10px 12px',
                  borderBottom: '2px solid #e2e8f0',
                  fontWeight: 600,
                  color: '#475569',
                  whiteSpace: 'nowrap',
                }}>
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={row.id || i}
                onClick={() => onRowClick?.(row)}
                style={{
                  cursor: onRowClick ? 'pointer' : 'default',
                  borderBottom: '1px solid #f1f5f9',
                  transition: 'background 0.1s',
                }}
                onMouseEnter={(e) => onRowClick && (e.currentTarget.style.background = '#f8fafc')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '')}
              >
                {columns.map((col) => (
                  <td key={col.key} style={{ padding: '10px 12px', whiteSpace: 'nowrap' }}>
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && (
          <div style={{ padding: 30, textAlign: 'center', color: '#94a3b8' }}>No data</div>
        )}
      </div>
    );
  }

  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        {children}
      </table>
    </div>
  );
}

export function Th({ children, style = {} }) {
  return (
    <th style={{
      textAlign: 'left',
      padding: '10px 12px',
      borderBottom: '2px solid #e2e8f0',
      fontWeight: 600,
      color: '#475569',
      whiteSpace: 'nowrap',
      fontSize: 13,
      ...style,
    }}>
      {children}
    </th>
  );
}

export function Td({ children, style = {} }) {
  return (
    <td style={{
      padding: '10px 12px',
      borderBottom: '1px solid #f1f5f9',
      color: '#1e293b',
      fontSize: 13,
      ...style,
    }}>
      {children}
    </td>
  );
}
