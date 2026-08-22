import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Layout from '../components/Layout';
import WorkflowStepper from '../components/WorkflowStepper';
import RiskBadge from '../components/RiskBadge';
import StatusBadge from '../components/StatusBadge';
import { Card, Loading, Error, Table, Button } from '../components/UI';

export default function Incidents() {
  const [incidents, setIncidents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const loadIncidents = () => {
    setLoading(true);
    api.listIncidents({ limit: 100 })
      .then((d) => setIncidents(d.items || []))
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadIncidents();
  }, []);

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#1e293b' }}>
            Autonomous Incident Control Tower
          </h1>
          <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>
            Monitor disruptions, track workflow progress across multi-agent stages & drill into recovery recommendations
          </p>
        </div>
        <span style={{ fontSize: 13, color: '#64748b', fontWeight: 600 }}>{incidents.length} active incidents</span>
      </div>

      <WorkflowStepper currentStep="supervisor" />

      {loading ? (
        <Loading />
      ) : error ? (
        <Error message={error} />
      ) : (
        <Card style={{ padding: 20 }}>
          <Table
            columns={[
              { key: 'incident_id', label: 'ID', render: (v) => <code style={{ fontSize: 12, fontWeight: 700 }}>{v?.slice(0, 8)}</code> },
              { key: 'incident_type', label: 'Disruption Type', render: (v) => v?.replace(/_/g, ' ') },
              { key: 'material_id', label: 'Material' },
              { key: 'severity', label: 'Risk Severity', render: (v) => <RiskBadge level={v} /> },
              { key: 'status', label: 'Workflow Stage', render: (v) => <StatusBadge status={v} /> },
              { key: 'created_at', label: 'Detected At', render: (v) => (v ? new Date(v).toLocaleTimeString() : '-') },
              {
                key: 'action',
                label: 'Action',
                render: (_, row) => (
                  <Button
                    onClick={() => navigate(`/incidents/${row.incident_id}`)}
                    style={{ fontSize: 12, padding: '4px 10px' }}
                  >
                    View Agent Timeline →
                  </Button>
                ),
              },
            ]}
            rows={incidents}
          />
        </Card>
      )}
    </Layout>
  );
}
