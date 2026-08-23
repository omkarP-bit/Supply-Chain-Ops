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
    setError(null);
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
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#1e293b' }}>
            Supply Chain Incident Queue
          </h1>
          <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>
            Monitor operational disruptions, review risk evaluations and authorize recovery actions
          </p>
        </div>
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <span style={{ fontSize: 13, color: '#64748b', fontWeight: 600 }}>{incidents.length} active incidents</span>
          <Button onClick={loadIncidents} style={{ background: '#ffffff', color: '#334155', border: '1px solid #cbd5e1', fontSize: 13 }}>
            ↻ Refresh Queue
          </Button>
        </div>
      </div>

      <WorkflowStepper currentStep="assess" />

      {loading ? (
        <Loading />
      ) : error ? (
        <Error message={error} />
      ) : (
        <Card style={{ padding: 20 }}>
          {incidents.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#64748b' }}>
              No incidents found in database.
            </div>
          ) : (
            <Table
              columns={[
                {
                  key: 'incident_id',
                  label: 'Incident ID',
                  render: (v) => <code style={{ fontSize: 12, fontWeight: 700, color: '#2563eb' }}>{v?.slice(0, 14)}</code>,
                },
                {
                  key: 'incident_type',
                  label: 'Disruption Type',
                  render: (v) => <strong style={{ color: '#0f172a' }}>{v?.replace(/_/g, ' ')}</strong>,
                },
                {
                  key: 'material_id',
                  label: 'Component',
                  render: (v) => <code>{v || 'COMP-104'}</code>,
                },
                {
                  key: 'po_id',
                  label: 'PO Ref',
                  render: (v) => (v ? <code>{v}</code> : <span style={{ color: '#94a3b8' }}>-</span>),
                },
                {
                  key: 'severity',
                  label: 'Risk Severity',
                  render: (v) => <RiskBadge level={v} />,
                },
                {
                  key: 'status',
                  label: 'Workflow Stage',
                  render: (v) => <StatusBadge status={v} />,
                },
                {
                  key: 'created_at',
                  label: 'Detected At',
                  render: (v) => (v ? new Date(v).toLocaleString() : '-'),
                },
                {
                  key: 'action',
                  label: 'Action',
                  render: (_, row) => (
                    <Button
                      onClick={() => navigate(`/incidents/${row.incident_id}`)}
                      style={{ fontSize: 12, padding: '6px 14px', background: '#2563eb' }}
                    >
                      Decision Dossier →
                    </Button>
                  ),
                },
              ]}
              rows={incidents}
            />
          )}
        </Card>
      )}
    </Layout>
  );
}
