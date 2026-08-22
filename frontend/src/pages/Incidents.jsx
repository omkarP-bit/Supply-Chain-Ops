import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Layout from '../components/Layout';
import RiskBadge from '../components/RiskBadge';
import StatusBadge from '../components/StatusBadge';
import { Card, Loading, Error, Table } from '../components/UI';

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    api.listIncidents({ limit: 100 })
      .then((d) => setIncidents(d.items || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Layout><Loading /></Layout>;
  if (error) return <Layout><Error message={error} /></Layout>;

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#1a1a2e' }}>Incidents</h2>
        <span style={{ fontSize: 14, color: '#666' }}>{incidents.length} total</span>
      </div>

      <Card>
        <Table
          columns={[
            { key: 'incident_id', label: 'ID', render: (v) => <code style={{ fontSize: 12 }}>{v?.slice(0, 8)}</code> },
            { key: 'incident_type', label: 'Type' },
            { key: 'material_id', label: 'Material' },
            { key: 'severity', label: 'Severity', render: (v) => <RiskBadge level={v} /> },
            { key: 'status', label: 'Status', render: (v) => <StatusBadge status={v} /> },
            { key: 'created_at', label: 'Created', render: (v) => v ? new Date(v).toLocaleString() : '-' },
          ]}
          rows={incidents}
          onRowClick={(row) => navigate(`/incidents/${row.incident_id}`)}
        />
      </Card>
    </Layout>
  );
}
