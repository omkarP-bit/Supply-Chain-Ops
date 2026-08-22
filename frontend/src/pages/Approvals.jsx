import React, { useState, useEffect } from 'react';
import api from '../services/api';
import Layout from '../components/Layout';
import { Card, Button, Spinner, Table, Th, Td } from '../components/UI';

export default function Approvals() {
  const [escalations, setEscalations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [error, setError] = useState(null);
  const [tab, setTab] = useState('pending'); // 'pending' | 'resolved'
  const [noteInputs, setNoteInputs] = useState({});

  const loadEscalations = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listEscalations();
      setEscalations(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEscalations();
  }, []);

  const handleResolve = async (escalationId, decision) => {
    try {
      setActionLoading(escalationId);
      const note = noteInputs[escalationId] || '';
      await api.resolveEscalation(escalationId, decision, note);
      await loadEscalations();
    } catch (err) {
      alert(`Resolution failed: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleNoteChange = (id, val) => {
    setNoteInputs((prev) => ({ ...prev, [id]: val }));
  };

  const pendingList = escalations.filter((e) => e.status === 'pending');
  const resolvedList = escalations.filter((e) => e.status !== 'pending');
  const currentList = tab === 'pending' ? pendingList : resolvedList;

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#1e293b' }}>
            Human Escalation & Approval Queue
          </h1>
          <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>
            Review high-cost purchase orders and critical operational deviations requiring manager sign-off
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setTab('pending')}
            style={{
              padding: '8px 16px',
              borderRadius: 6,
              border: 'none',
              background: tab === 'pending' ? '#1e293b' : '#e2e8f0',
              color: tab === 'pending' ? '#fff' : '#475569',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Pending ({pendingList.length})
          </button>
          <button
            onClick={() => setTab('resolved')}
            style={{
              padding: '8px 16px',
              borderRadius: 6,
              border: 'none',
              background: tab === 'resolved' ? '#1e293b' : '#e2e8f0',
              color: tab === 'resolved' ? '#fff' : '#475569',
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            Resolved History ({resolvedList.length})
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: 14, background: '#fee2e2', color: '#991b1b', borderRadius: 8, marginBottom: 20 }}>
          {error}
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}><Spinner size="lg" /></div>
      ) : currentList.length === 0 ? (
        <Card style={{ padding: 40, textAlign: 'center', color: '#64748b' }}>
          {tab === 'pending'
            ? 'No pending escalations. All operational alerts are within normal thresholds.'
            : 'No resolved escalation history yet.'}
        </Card>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {currentList.map((esc) => (
            <Card key={esc.escalation_id} style={{ padding: 20, borderLeft: `5px solid ${esc.status === 'pending' ? '#f59e0b' : esc.status === 'approved' ? '#10b981' : '#ef4444'}` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 12 }}>
                <div style={{ flex: 1, minWidth: 280 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: 4,
                        fontSize: 11,
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        background: esc.status === 'pending' ? '#fef3c7' : esc.status === 'approved' ? '#d1fae5' : '#fee2e2',
                        color: esc.status === 'pending' ? '#b45309' : esc.status === 'approved' ? '#065f46' : '#991b1b',
                      }}
                    >
                      {esc.status}
                    </span>
                    <span style={{ fontSize: 12, color: '#64748b' }}>
                      ID: <code>{esc.escalation_id.slice(0, 8)}</code>
                    </span>
                    <span style={{ fontSize: 12, color: '#64748b' }}>•</span>
                    <span style={{ fontSize: 12, color: '#64748b' }}>
                      Created: {new Date(esc.created_at).toLocaleString()}
                    </span>
                  </div>

                  <h3 style={{ margin: '0 0 8px', fontSize: 16, color: '#0f172a', fontWeight: 600 }}>
                    {esc.brief}
                  </h3>

                  {esc.cost_delta !== null && (
                    <div style={{ display: 'inline-block', background: '#f1f5f9', padding: '4px 10px', borderRadius: 4, fontSize: 13, color: '#334155', marginBottom: 8 }}>
                      <strong>Threshold Delta:</strong> +INR {Number(esc.cost_delta).toLocaleString()}
                    </div>
                  )}

                  {esc.resolved_by && (
                    <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
                      Resolved by <strong>{esc.resolved_by}</strong> at {new Date(esc.resolved_at).toLocaleString()}
                    </div>
                  )}
                </div>

                {esc.status === 'pending' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8, minWidth: 260 }}>
                    <input
                      type="text"
                      placeholder="Optional approval/rejection notes..."
                      value={noteInputs[esc.escalation_id] || ''}
                      onChange={(e) => handleNoteChange(esc.escalation_id, e.target.value)}
                      style={{
                        padding: '8px 12px',
                        border: '1px solid #cbd5e1',
                        borderRadius: 6,
                        fontSize: 13,
                        outline: 'none',
                      }}
                    />
                    <div style={{ display: 'flex', gap: 8 }}>
                      <Button
                        onClick={() => handleResolve(esc.escalation_id, 'approve')}
                        disabled={actionLoading === esc.escalation_id}
                        style={{
                          flex: 1,
                          background: '#10b981',
                          borderColor: '#10b981',
                          color: '#fff',
                          fontWeight: 600,
                        }}
                      >
                        {actionLoading === esc.escalation_id ? <Spinner size="sm" /> : '✓ Approve'}
                      </Button>
                      <Button
                        onClick={() => handleResolve(esc.escalation_id, 'reject')}
                        disabled={actionLoading === esc.escalation_id}
                        style={{
                          flex: 1,
                          background: '#ef4444',
                          borderColor: '#ef4444',
                          color: '#fff',
                          fontWeight: 600,
                        }}
                      >
                        {actionLoading === esc.escalation_id ? <Spinner size="sm" /> : '✕ Reject'}
                      </Button>
                    </div>
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
