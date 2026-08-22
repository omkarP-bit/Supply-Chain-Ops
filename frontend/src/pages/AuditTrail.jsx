import React, { useState, useEffect } from 'react';
import api from '../services/api';
import Layout from '../components/Layout';
import { Card, Spinner, Table, Th, Td } from '../components/UI';

export default function AuditTrail() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchEntity, setSearchEntity] = useState('');
  const [selectedType, setSelectedType] = useState('ALL');
  const [error, setError] = useState(null);
  const [selectedLog, setSelectedLog] = useState(null);

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = searchEntity ? { entity_id: searchEntity } : {};
      const data = await api.getAuditLog(params);
      setLogs(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAuditLogs();
  }, [searchEntity]);

  const filteredLogs = selectedType === 'ALL'
    ? logs
    : logs.filter((l) => l.event_type === selectedType);

  const eventTypes = ['ALL', ...Array.from(new Set(logs.map((l) => l.event_type)))];

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24, flexWrap: 'wrap', gap: 16 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#1e293b' }}>
            System Audit & Governance Trail
          </h1>
          <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>
            Immutable chronological record of automated agent actions, rule evaluations, and human decisions
          </p>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Filter by entity ID (e.g. PO-7712)..."
            value={searchEntity}
            onChange={(e) => setSearchEntity(e.target.value)}
            style={{
              padding: '8px 14px',
              border: '1px solid #cbd5e1',
              borderRadius: 6,
              fontSize: 13,
              width: 250,
              outline: 'none',
            }}
          />
        </div>
      </div>

      {error && (
        <div style={{ padding: 14, background: '#fee2e2', color: '#991b1b', borderRadius: 8, marginBottom: 20 }}>
          {error}
        </div>
      )}

      {/* Filter Chips */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 16, flexWrap: 'wrap' }}>
        {eventTypes.map((type) => (
          <button
            key={type}
            onClick={() => setSelectedType(type)}
            style={{
              padding: '6px 12px',
              borderRadius: 6,
              border: '1px solid #cbd5e1',
              background: selectedType === type ? '#1e293b' : '#fff',
              color: selectedType === type ? '#fff' : '#475569',
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            {type === 'ALL' ? 'All Events' : type}
          </button>
        ))}
      </div>

      {/* Audit Log Table */}
      <Card style={{ padding: 20 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 60 }}><Spinner size="lg" /></div>
        ) : filteredLogs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#64748b' }}>
            No audit events found. Run an alert scan or approve an escalation to generate log events.
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Timestamp</Th>
                <Th>Event Type</Th>
                <Th>Entity</Th>
                <Th>Actor</Th>
                <Th>State Change Details</Th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log) => (
                <tr key={log.audit_id}>
                  <Td style={{ fontSize: 12, color: '#64748b', whiteSpace: 'nowrap' }}>
                    {new Date(log.ts).toLocaleString()}
                  </Td>
                  <Td>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: 4,
                        fontSize: 11,
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        background:
                          log.event_type === 'escalation_resolved'
                            ? '#d1fae5'
                            : log.event_type === 'escalation_created'
                            ? '#fef3c7'
                            : '#ede9fe',
                        color:
                          log.event_type === 'escalation_resolved'
                            ? '#065f46'
                            : log.event_type === 'escalation_created'
                            ? '#b45309'
                            : '#6d28d9',
                      }}
                    >
                      {log.event_type}
                    </span>
                  </Td>
                  <Td>
                    <code style={{ background: '#f1f5f9', padding: '2px 6px', borderRadius: 4 }}>
                      {log.entity_type}:{log.entity_id}
                    </code>
                  </Td>
                  <Td>
                    {log.actor ? (
                      <strong style={{ color: '#0f172a' }}>{log.actor}</strong>
                    ) : (
                      <span style={{ color: '#94a3b8', fontStyle: 'italic' }}>System / Autonomous</span>
                    )}
                  </Td>
                  <Td>
                    <button
                      onClick={() => setSelectedLog(log)}
                      style={{
                        padding: '4px 10px',
                        fontSize: 12,
                        background: '#f8fafc',
                        border: '1px solid #cbd5e1',
                        borderRadius: 4,
                        cursor: 'pointer',
                        fontWeight: 600,
                        color: '#2563eb',
                      }}
                    >
                      Inspect JSON Payload
                    </button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      {/* JSON Payload Modal */}
      {selectedLog && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setSelectedLog(null)}
        >
          <div
            style={{
              background: '#fff',
              padding: 24,
              borderRadius: 8,
              maxWidth: 600,
              width: '90%',
              maxHeight: '80vh',
              overflowY: 'auto',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <h3 style={{ margin: 0, fontSize: 18, color: '#1e293b' }}>
                Audit Event: {selectedLog.event_type}
              </h3>
              <button
                onClick={() => setSelectedLog(null)}
                style={{ border: 'none', background: 'transparent', fontSize: 18, cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{ marginBottom: 12, fontSize: 13 }}>
              <strong>Entity:</strong> {selectedLog.entity_type}:{selectedLog.entity_id} | <strong>Actor:</strong> {selectedLog.actor || 'System'}
            </div>

            {selectedLog.before && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 4 }}>Before State:</div>
                <pre style={{ background: '#f8fafc', padding: 10, borderRadius: 6, fontSize: 12, overflowX: 'auto' }}>
                  {JSON.stringify(selectedLog.before, null, 2)}
                </pre>
              </div>
            )}

            {selectedLog.after && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#64748b', marginBottom: 4 }}>After / Captured State:</div>
                <pre style={{ background: '#f8fafc', padding: 10, borderRadius: 6, fontSize: 12, overflowX: 'auto' }}>
                  {JSON.stringify(selectedLog.after, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}
