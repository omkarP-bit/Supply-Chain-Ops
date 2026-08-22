import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Layout from '../components/Layout';
import RiskBadge from '../components/RiskBadge';
import StatusBadge from '../components/StatusBadge';
import { Card, StatCard, Loading, Error, Table } from '../components/UI';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.getDashboard()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Layout><Loading /></Layout>;
  if (error) return <Layout><Error message={error} /></Layout>;

  const stats = [
    { label: 'Active Incidents', value: data.active_incidents_count, color: '#1565c0' },
    { label: 'Critical Risk', value: data.critical_risk_count, color: '#c62828' },
    { label: 'Pending Approvals', value: data.pending_approvals_count, color: '#f57f17' },
    { label: 'Production at Risk', value: data.production_at_risk.length, color: '#e65100' },
  ];

  return (
    <Layout>
      <h2 style={{ margin: '0 0 20px', fontSize: 22, fontWeight: 700, color: '#1a1a2e' }}>Dashboard</h2>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16, marginBottom: 24 }}>
        {stats.map((s) => <StatCard key={s.label} {...s} />)}
      </div>

      {data.production_at_risk.length > 0 && (
        <Card style={{ marginBottom: 20 }}>
          <h3 style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 600, color: '#e65100' }}>Production at Risk</h3>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {data.production_at_risk.map((mid) => (
              <span key={mid} style={{
                padding: '4px 12px',
                background: '#fff3e0',
                border: '1px solid #ffcc80',
                borderRadius: 6,
                fontSize: 13,
                fontWeight: 600,
                color: '#e65100',
              }}>{mid}</span>
            ))}
          </div>
        </Card>
      )}

      <Card>
        <h3 style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 600 }}>Recent Incidents</h3>
        <Table
          columns={[
            { key: 'incident_id', label: 'ID', render: (v) => <code style={{ fontSize: 12 }}>{v?.slice(0, 8)}</code> },
            { key: 'incident_type', label: 'Type' },
            { key: 'material_id', label: 'Material' },
            { key: 'severity', label: 'Severity', render: (v) => <RiskBadge level={v} /> },
            { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
            { key: 'created_at', label: 'Created', render: (v) => v ? new Date(v).toLocaleString() : '-' },
          ]}
          rows={data.recent_incidents || []}
          onRowClick={(row) => navigate(`/incidents/${row.incident_id}`)}
        />
      </Card>
    </Layout>
  );
}
