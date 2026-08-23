import React from 'react';

export function Spinner({ size = 'md' }) {
  const s = size === 'sm' ? 14 : size === 'lg' ? 24 : 18;
  return (
    <div
      style={{
        display: 'inline-block',
        width: s,
        height: s,
        border: '2px solid rgba(255,255,255,0.3)',
        borderTopColor: '#ffffff',
        borderRadius: '50%',
        animation: 'spin 0.6s linear infinite',
      }}
    />
  );
}

export function Loading() {
  return (
    <div style={{ padding: 48, textAlign: 'center', color: '#8A919B', fontFamily: 'var(--font-mono)' }}>
      INITIALIZING SYSTEM TELEMETRY...
    </div>
  );
}

export function Error({ message }) {
  return (
    <div style={{ padding: 16, background: '#FFFFFF', borderRadius: 8, color: '#C4302B', border: '1px solid #D5D8DC', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
      [SYSTEM ERROR] {message || 'Operational failure detected.'}
    </div>
  );
}

export function Card({ children, style = {} }) {
  return (
    <div
      style={{
        background: '#FFFFFF',
        borderRadius: 8,
        padding: 20,
        border: '1px solid #D5D8DC',
        boxShadow: 'none',
        ...style,
      }}
    >
      {children}
    </div>
  );
}

export function StatCard({ label, value, color }) {
  return (
    <Card style={{ textAlign: 'left', minWidth: 140 }}>
      <div style={{ fontSize: 11, color: '#8A919B', textTransform: 'uppercase', letterSpacing: 0.5, fontWeight: 600 }}>
        {label}
      </div>
      <div style={{ fontSize: 24, fontWeight: 700, color: color || '#12161C', marginTop: 4, fontFamily: 'var(--font-heading)' }}>
        {value}
      </div>
    </Card>
  );
}

export function Button({ children, onClick, disabled = false, variant = 'primary', style = {} }) {
  const isPrimary = variant === 'primary';
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 6,
        padding: '7px 16px',
        background: isPrimary ? '#003DA5' : '#FFFFFF',
        color: isPrimary ? '#FFFFFF' : '#12161C',
        border: isPrimary ? '1px solid #003DA5' : '1px solid #D5D8DC',
        borderRadius: 6,
        fontSize: 13,
        fontWeight: 600,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1,
        transition: 'all 0.15s ease',
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
            <tr style={{ background: '#F4F5F7' }}>
              {columns.map((col) => (
                <th
                  key={col.key}
                  style={{
                    textAlign: 'left',
                    padding: '9px 12px',
                    borderBottom: '1px solid #D5D8DC',
                    fontWeight: 700,
                    color: '#3A4149',
                    fontSize: 11,
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                    whiteSpace: 'nowrap',
                  }}
                >
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
                  borderBottom: '1px solid #D5D8DC',
                  transition: 'background 0.1s',
                }}
                onMouseEnter={(e) => onRowClick && (e.currentTarget.style.background = '#F4F5F7')}
                onMouseLeave={(e) => (e.currentTarget.style.background = '')}
              >
                {columns.map((col) => (
                  <td key={col.key} style={{ padding: '10px 12px', whiteSpace: 'nowrap', color: '#12161C' }}>
                    {col.render ? col.render(row[col.key], row) : row[col.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && (
          <div style={{ padding: 30, textAlign: 'center', color: '#8A919B', fontFamily: 'var(--font-mono)' }}>NO RECORDS IDENTIFIED</div>
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
    <th
      style={{
        textAlign: 'left',
        padding: '9px 12px',
        background: '#F4F5F7',
        borderBottom: '1px solid #D5D8DC',
        fontWeight: 700,
        color: '#3A4149',
        fontSize: 11,
        textTransform: 'uppercase',
        letterSpacing: 0.5,
        whiteSpace: 'nowrap',
        ...style,
      }}
    >
      {children}
    </th>
  );
}

export function Td({ children, style = {} }) {
  return (
    <td
      style={{
        padding: '10px 12px',
        borderBottom: '1px solid #D5D8DC',
        color: '#12161C',
        fontSize: 13,
        ...style,
      }}
    >
      {children}
    </td>
  );
}
