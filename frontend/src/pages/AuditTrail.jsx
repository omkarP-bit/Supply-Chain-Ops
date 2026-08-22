import React, { useEffect, useState } from 'react';
import api from '../services/api';
import Layout from '../components/Layout';
import RiskBadge from '../components/RiskBadge';
import { Card, Loading, Error } from '../components/UI';

export default function AuditTrail() {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.listAuditEvents({ limit: 200 })
      .then(setEvents)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Layout><Loading /></Layout>;
  if (error) return <Layout><Error message={error} /></Layout>;

  return (
    <Layout>
      <h2 style={{ margin: '0 0 20px', fontSize: 22, fontWeight: 700, color: '#1a1a2e' }}>Audit Trail</h2>

      {events.length === 0 ? (
        <Card>
          <div style={{ padding: 30, textAlign: 'center', color: '#999' }}>
            No audit events yet. Run the recovery workflow to generate audit entries.
          </div>
        </Card>
      ) : (
        <div style={{ position: 'relative' }}>
          <div style={{
            position: 'absolute', left: 20, top: 0, bottom: 0,
            width: 2, background: '#e0e0e0',
          }} />
          <div style={{ display: 'grid', gap: 12 }}>
            {events.map((e, i) => (
              <div key={e.event_id || i} style={{ display: 'flex', gap: 16, paddingLeft: 8 }}>
                <div style={{
                  width: 24, height: 24, borderRadius: '50%', flexShrink: 0,
                  background: e.risk_level === 'CRITICAL' ? '#c62828' :
                    e.event_type === 'APPROVAL' ? '#2e7d32' : '#1565c0',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontSize: 10, fontWeight: 700, marginTop: 2,
                }}>
                  {e.event_type?.[0]}
                </div>
                <Card style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                      <strong style={{ fontSize: 13 }}>{e.action}</strong>
                      <span style={{ fontSize: 12, color: '#666' }}>{e.event_type}</span>
                      {e.risk_level && <RiskBadge level={e.risk_level} />}
                    </div>
                    <span style={{ fontSize: 11, color: '#999' }}>
                      {e.timestamp ? new Date(e.timestamp).toLocaleString() : '-'}
                    </span>
                  </div>
                  <div style={{ fontSize: 12, color: '#555' }}>
                    <span>Agent: <strong>{e.agent_name}</strong></span>
                    {e.incident_id && <span> | Incident: <code>{e.incident_id?.slice(0, 8)}</code></span>}
                  </div>
                  {e.reason && (
                    <div style={{ marginTop: 4, fontSize: 12, color: '#c62828', fontStyle: 'italic' }}>
                      {e.reason}
                    </div>
                  )}
                  {e.output_data && (
                    <div style={{
                      marginTop: 6, fontSize: 11, background: '#f5f5f5', padding: 6,
                      borderRadius: 4, fontFamily: 'monospace', whiteSpace: 'pre-wrap',
                    }}>
                      {JSON.stringify(e.output_data, null, 2)}
                    </div>
                  )}
                </Card>
              </div>
            ))}
          </div>
        </div>
      )}
    </Layout>
  );
}
