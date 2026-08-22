import React, { useEffect, useState } from 'react';
import api from '../services/api';
import Layout from '../components/Layout';
import StatusBadge from '../components/StatusBadge';
import { Card, Loading, Error, Table } from '../components/UI';

export default function Suppliers() {
  const [suppliers, setSuppliers] = useState([]);
  const [eligible, setEligible] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    Promise.all([
      api.listSuppliers(),
      api.getEligibleSuppliers('COMP-104', 800).catch(() => []),
    ])
      .then(([all, elig]) => { setSuppliers(all); setEligible(elig); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Layout><Loading /></Layout>;
  if (error) return <Layout><Error message={error} /></Layout>;

  const eligibleIds = new Set(eligible.map((e) => e.supplier_id));

  const rows = suppliers.map((s) => ({
    ...s,
    isEligible: eligibleIds.has(s.supplier_id),
    eligibleData: eligible.find((e) => e.supplier_id === s.supplier_id),
  }));

  const filtered = filter === 'all' ? rows
    : filter === 'eligible' ? rows.filter((r) => r.isEligible)
    : rows.filter((r) => !r.isEligible);

  return (
    <Layout>
      <h2 style={{ margin: '0 0 8px', fontSize: 22, fontWeight: 700, color: '#1a1a2e' }}>Supplier Comparison</h2>
      <p style={{ margin: '0 0 16px', fontSize: 13, color: '#666' }}>
        Eligibility for COMP-104, qty=800 units
      </p>

      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        {['all', 'eligible', 'rejected'].map((f) => (
          <button key={f} onClick={() => setFilter(f)} style={{
            padding: '6px 14px', borderRadius: 6, border: '1px solid #ddd',
            background: filter === f ? '#1a1a2e' : '#fff',
            color: filter === f ? '#fff' : '#333',
            fontSize: 13, fontWeight: 600, cursor: 'pointer',
          }}>{f.charAt(0).toUpperCase() + f.slice(1)}</button>
        ))}
      </div>

      <Card>
        <Table
          columns={[
            { key: 'supplier_id', label: 'ID' },
            { key: 'supplier_name', label: 'Name' },
            { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
            { key: 'quality_score', label: 'Quality' },
            { key: 'overall_reliability_score', label: 'Reliability' },
            { key: 'on_time_delivery_rate', label: 'On-Time %', render: (v) => v ? `${(parseFloat(v) * 100).toFixed(1)}%` : '-' },
            {
              key: 'eligible',
              label: 'Eligible (COMP-104)',
              render: (_, row) => {
                if (!row.eligibleData) return <span style={{ color: '#999', fontSize: 12 }}>N/A</span>;
                const ed = row.eligibleData;
                if (ed.rejection_reason) {
                  return <span style={{ color: '#c62828', fontSize: 12 }}>{ed.rejection_reason}</span>;
                }
                return (
                  <span style={{ color: '#2e7d32', fontSize: 12 }}>
                    Score: {ed.score} | ₹{ed.unit_price} | {ed.lead_time_days}d | {ed.available_quantity}u
                  </span>
                );
              },
            },
          ]}
          rows={filtered}
        />
      </Card>
    </Layout>
  );
}
