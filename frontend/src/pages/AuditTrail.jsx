import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import api from '../services/api';
import Layout from '../components/Layout';
import { Card, Spinner, Table, Th, Td, Button } from '../components/UI';

export default function AuditTrail() {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialEntity = searchParams.get('entity_id') || searchParams.get('incident_id') || '';

  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchEntity, setSearchEntity] = useState(initialEntity);
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

  const eventTypes = ['ALL', ...Array.from(new Set(logs.map((l) => l.event_type).filter(Boolean)))];

  const getEventTextColor = (type) => {
    if (!type) return '#3A4149';
    const t = type.toUpperCase();
    if (t.includes('PASS') || t.includes('RESOLVED') || t.includes('AUTHORIZED') || t.includes('SUCCESS')) return '#1E8E5A';
    if (t.includes('FAIL') || t.includes('REJECT') || t.includes('CRITICAL') || t.includes('SHUTDOWN')) return '#C4302B';
    if (t.includes('APPROVAL') || t.includes('PENDING') || t.includes('DELAY') || t.includes('RISK')) return '#B98900';
    return '#3A4149';
  };

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#12161C', textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Audit & Governance Log
          </h1>
          <p style={{ margin: '2px 0 0', color: '#8A919B', fontSize: 12 }}>
            Immutable chronological record of automated agent reasoning, constraint checks & human authorizations
          </p>
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Filter by entity / incident ID..."
            value={searchEntity}
            onChange={(e) => setSearchEntity(e.target.value)}
            style={{
              padding: '6px 12px',
              border: '1px solid #D5D8DC',
              borderRadius: 4,
              fontSize: 12,
              width: 240,
              outline: 'none',
              fontFamily: 'var(--font-mono)',
              background: '#FFFFFF',
            }}
          />
          <Button onClick={loadAuditLogs} variant="secondary" style={{ fontSize: 12, padding: '6px 12px' }}>
            ↻ Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div style={{ padding: 12, background: '#FFFFFF', color: '#C4302B', borderRadius: 6, marginBottom: 16, border: '1px solid #D5D8DC', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          [AUDIT FAULT] {error}
        </div>
      )}

      {/* Filter Chips */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
        {eventTypes.map((type) => (
          <button
            key={type}
            onClick={() => setSelectedType(type)}
            style={{
              padding: '5px 10px',
              borderRadius: 4,
              border: '1px solid #D5D8DC',
              background: selectedType === type ? '#12161C' : '#FFFFFF',
              color: selectedType === type ? '#FFFFFF' : '#3A4149',
              fontSize: 11,
              fontWeight: 600,
              fontFamily: 'var(--font-mono)',
              cursor: 'pointer',
            }}
          >
            {type === 'ALL' ? 'ALL EVENTS' : type}
          </button>
        ))}
      </div>

      {/* Audit Log Table */}
      <Card style={{ padding: 18 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 50, color: '#8A919B', fontFamily: 'var(--font-mono)' }}><Spinner size="lg" /></div>
        ) : filteredLogs.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 30, color: '#8A919B', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
            NO AUDIT RECORDS FOUND FOR QUERY.
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Timestamp</Th>
                <Th>Event Type</Th>
                <Th>Entity Reference</Th>
                <Th>Agent / Actor</Th>
                <Th>Action & State Outcome</Th>
                <Th>Telemetry</Th>
              </tr>
            </thead>
            <tbody>
              {filteredLogs.map((log, idx) => (
                <tr key={log.audit_id || idx}>
                  <Td style={{ fontSize: 11, color: '#8A919B', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                    {log.ts ? new Date(log.ts).toLocaleString() : '-'}
                  </Td>
                  <Td>
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        fontFamily: 'var(--font-mono)',
                        color: getEventTextColor(log.event_type),
                      }}
                    >
                      ● {log.event_type}
                    </span>
                  </Td>
                  <Td>
                    <code style={{ color: '#003DA5', fontWeight: 600 }}>
                      {log.entity_type}:{log.entity_id}
                    </code>
                  </Td>
                  <Td>
                    <strong style={{ color: '#12161C', fontSize: 12, fontFamily: 'var(--font-mono)' }}>{log.actor}</strong>
                  </Td>
                  <Td style={{ fontSize: 12, color: '#3A4149', maxWidth: 300 }}>
                    {log.action ? (
                      <div>
                        <strong>{log.action}</strong>
                        {log.reason && <div style={{ color: '#8A919B', fontSize: 11 }}>{log.reason}</div>}
                      </div>
                    ) : (
                      <span>{log.reason || JSON.stringify(log.details)?.slice(0, 80) || '-'}</span>
                    )}
                  </Td>
                  <Td>
                    <button
                      onClick={() => setSelectedLog(log)}
                      style={{
                        padding: '4px 8px',
                        fontSize: 11,
                        background: '#F4F5F7',
                        border: '1px solid #D5D8DC',
                        borderRadius: 4,
                        cursor: 'pointer',
                        fontWeight: 600,
                        color: '#003DA5',
                        fontFamily: 'var(--font-mono)',
                      }}
                    >
                      INSPECT
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
            background: 'rgba(18,22,28,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setSelectedLog(null)}
        >
          <div
            style={{
              background: '#FFFFFF',
              padding: 20,
              borderRadius: 8,
              maxWidth: 650,
              width: '90%',
              maxHeight: '80vh',
              overflowY: 'auto',
              border: '1px solid #D5D8DC',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, borderBottom: '1px solid #D5D8DC', paddingBottom: 10 }}>
              <h3 style={{ margin: 0, fontSize: 15, color: '#12161C', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
                AUDIT TELEMETRY: {selectedLog.event_type}
              </h3>
              <button
                onClick={() => setSelectedLog(null)}
                style={{ border: 'none', background: 'transparent', fontSize: 16, cursor: 'pointer', color: '#8A919B' }}
              >
                ✕
              </button>
            </div>

            <div style={{ marginBottom: 12, fontSize: 12, background: '#F4F5F7', padding: 8, borderRadius: 4, fontFamily: 'var(--font-mono)' }}>
              <strong>ENTITY:</strong> <code>{selectedLog.entity_type}:{selectedLog.entity_id}</code> | <strong>ACTOR:</strong> {selectedLog.actor}
            </div>

            {selectedLog.before && Object.keys(selectedLog.before).length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#8A919B', textTransform: 'uppercase', marginBottom: 4 }}>Before / Input State:</div>
                <pre style={{ background: '#F4F5F7', padding: 10, borderRadius: 4, fontSize: 11, border: '1px solid #D5D8DC', overflowX: 'auto', fontFamily: 'var(--font-mono)' }}>
                  {JSON.stringify(selectedLog.before, null, 2)}
                </pre>
              </div>
            )}

            {selectedLog.after && Object.keys(selectedLog.after).length > 0 && (
              <div style={{ marginBottom: 12 }}>
                <div style={{ fontSize: 11, fontWeight: 700, color: '#8A919B', textTransform: 'uppercase', marginBottom: 4 }}>After / Captured State:</div>
                <pre style={{ background: '#F4F5F7', padding: 10, borderRadius: 4, fontSize: 11, border: '1px solid #D5D8DC', overflowX: 'auto', fontFamily: 'var(--font-mono)' }}>
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
