import React, { useEffect, useState } from 'react';
import api from '../services/api';
import Layout from '../components/Layout';
import StatusBadge from '../components/StatusBadge';
import { Card, Loading, Error } from '../components/UI';

export default function Approvals() {
  const [approvals, setApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [acting, setActing] = useState(null);

  const refresh = () => {
    setLoading(true);
    api.listApprovals()
      .then(setApprovals)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(refresh, []);

  const handleApprove = async (id) => {
    setActing(id);
    try {
      await api.approveRequest(id);
      refresh();
    } catch (e) { alert(e.message); }
    setActing(null);
  };

  const handleReject = async (id) => {
    const reason = prompt('Rejection reason:');
    if (reason === null) return;
    setActing(id);
    try {
      await api.rejectRequest(id, reason);
      refresh();
    } catch (e) { alert(e.message); }
    setActing(null);
  };

  if (loading) return <Layout><Loading /></Layout>;
  if (error) return <Layout><Error message={error} /></Layout>;

  return (
    <Layout>
      <h2 style={{ margin: '0 0 20px', fontSize: 22, fontWeight: 700, color: '#1a1a2e' }}>Approval Queue</h2>

      {approvals.length === 0 ? (
        <Card>
          <div style={{ padding: 30, textAlign: 'center', color: '#999' }}>
            No pending approvals
          </div>
        </Card>
      ) : (
        <div style={{ display: 'grid', gap: 12 }}>
          {approvals.map((a) => (
            <Card key={a.approval_id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8 }}>
                    <StatusBadge status={a.status} />
                    <code style={{ fontSize: 12 }}>{a.approval_id?.slice(0, 8)}</code>
                    <span style={{ fontSize: 12, color: '#666' }}>
                      Incident: {a.incident_id?.slice(0, 8)}
                    </span>
                  </div>
                  <div style={{ fontSize: 13, color: '#444' }}>
                    <div><strong>Plan:</strong> {a.plan_id?.slice(0, 8)}</div>
                    <div><strong>Type:</strong> {a.approval_type}</div>
                    {a.requested_at && <div><strong>Requested:</strong> {new Date(a.requested_at).toLocaleString()}</div>}
                  </div>
                </div>

                {a.status === 'PENDING' && (
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={() => handleApprove(a.approval_id)} disabled={acting === a.approval_id} style={{
                      padding: '6px 14px', borderRadius: 6, border: '1px solid #2e7d32', background: '#2e7d32',
                      color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer',
                    }}>Approve</button>
                    <button onClick={() => handleReject(a.approval_id)} disabled={acting === a.approval_id} style={{
                      padding: '6px 14px', borderRadius: 6, border: '1px solid #c62828', background: '#fff',
                      color: '#c62828', fontSize: 13, fontWeight: 600, cursor: 'pointer',
                    }}>Reject</button>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </Layout>
  );
}
