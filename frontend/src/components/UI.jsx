import React from 'react';

export function Loading() {
  return (
    <div style={{ padding: 40, textAlign: 'center', color: '#999' }}>
      Loading...
    </div>
  );
}

export function Error({ message }) {
  return (
    <div style={{ padding: 20, background: '#ffebee', borderRadius: 8, color: '#c62828', border: '1px solid #ef9a9a' }}>
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
      boxShadow: '0 1px 3px rgba(0,0,0,0.08)',
      border: '1px solid #e8e8e8',
      ...style,
    }}>
      {children}
    </div>
  );
}

export function StatCard({ label, value, color }) {
  return (
    <Card style={{ textAlign: 'center', minWidth: 140 }}>
      <div style={{ fontSize: 28, fontWeight: 700, color: color || '#1a1a2e' }}>{value}</div>
      <div style={{ fontSize: 13, color: '#666', marginTop: 4 }}>{label}</div>
    </Card>
  );
}

export function Table({ columns, rows, onRowClick }) {
  return (
    <div style={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 14 }}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col.key} style={{
                textAlign: 'left',
                padding: '10px 12px',
                borderBottom: '2px solid #e0e0e0',
                fontWeight: 600,
                color: '#555',
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
                borderBottom: '1px solid #f0f0f0',
                transition: 'background 0.1s',
              }}
              onMouseEnter={(e) => onRowClick && (e.currentTarget.style.background = '#f8f9fa')}
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
        <div style={{ padding: 30, textAlign: 'center', color: '#999' }}>No data</div>
      )}
    </div>
  );
}
