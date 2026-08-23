import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Layout from '../components/Layout';
import RiskBadge from '../components/RiskBadge';
import { Card, Button, Spinner, Table, Th, Td } from '../components/UI';

const formatDisruptionType = (type) => {
  if (!type) return 'OPERATIONAL DISRUPTION';
  return type.replace(/_/g, ' ').toUpperCase();
};

const getStageTextColor = (stage) => {
  if (!stage) return '#3A4149';
  const s = stage.toUpperCase();
  if (s === 'RESOLVED' || s === 'COMPLETED') return '#1E8E5A';
  if (s === 'REPLANNING' || s === 'ANALYZING' || s === 'AWAITING_APPROVAL') return '#B98900';
  if (s === 'CRITICAL' || s === 'FAILED') return '#C4302B';
  return '#3A4149';
};

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);

  const navigate = useNavigate();

  const loadDashboard = async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true);
      else setLoading(true);
      setError(null);
      const res = await api.getDashboard();
      setData(res);
    } catch (err) {
      setError(err.message || 'Unable to establish connection to operational telemetry API');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  const handleScan = async () => {
    try {
      setRefreshing(true);
      await api.scanAlerts();
      await loadDashboard(true);
    } catch (err) {
      alert(`System scan failure: ${err.message}`);
      setRefreshing(false);
    }
  };

  const topProductionRisks = data?.production_at_risk?.slice(0, 3) || [];

  return (
    <Layout>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: '#12161C', letterSpacing: -0.3 }}>
            Syntra AI
          </h1>
          <p style={{ margin: '3px 0 0', color: '#8A919B', fontSize: 13 }}>
            Tata Motors Autonomous Supply Chain Disruption Control Tower
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Button
            onClick={handleScan}
            disabled={refreshing}
            variant="primary"
            style={{ fontSize: 12, padding: '7px 14px' }}
          >
            {refreshing ? <Spinner size="sm" /> : '⚡'}
            {refreshing ? 'Evaluating Telemetry...' : 'Run Disruption Scan'}
          </Button>
          <Button
            onClick={() => loadDashboard(true)}
            disabled={refreshing}
            variant="secondary"
            style={{ fontSize: 12, padding: '7px 12px' }}
          >
            ↻ Refresh
          </Button>
        </div>
      </div>

      {/* Error State */}
      {error && (
        <div style={{ padding: 14, background: '#FFFFFF', color: '#C4302B', borderRadius: 6, marginBottom: 20, border: '1px solid #D5D8DC', fontFamily: 'var(--font-mono)', fontSize: 13 }}>
          <div style={{ fontWeight: 700, marginBottom: 4 }}>[CONTROL TOWER FAULT] Unable to load operational data</div>
          <div style={{ fontSize: 12, color: '#3A4149' }}>{error}</div>
          <div style={{ marginTop: 10 }}>
            <Button onClick={() => loadDashboard(true)} variant="secondary" style={{ fontSize: 11, padding: '4px 10px' }}>
              Retry Connection
            </Button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {loading && !data ? (
        <div style={{ textAlign: 'center', padding: 80, color: '#8A919B', fontFamily: 'var(--font-mono)' }}>
          <Spinner size="lg" />
          <div style={{ marginTop: 14, fontSize: 13 }}>INITIALIZING SYSTEM TELEMETRY...</div>
        </div>
      ) : data ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
          
          {/* 1. TOP KPI CARDS (Real backend state) */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
            <div style={{ background: '#FFFFFF', padding: '12px 16px', borderRadius: 8, border: '1px solid #D5D8DC' }}>
              <div style={{ fontSize: 11, color: '#8A919B', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>
                Active Incidents
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#12161C', marginTop: 3, fontFamily: 'var(--font-mono)' }}>
                {data.status_summary?.ACTIVE ?? data.active_incidents_count ?? 0}
              </div>
            </div>

            <div style={{ background: '#FFFFFF', padding: '12px 16px', borderRadius: 8, border: '1px solid #D5D8DC' }}>
              <div style={{ fontSize: 11, color: '#8A919B', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>
                Pending Sign-offs
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: (data.status_summary?.AWAITING_APPROVAL || data.pending_approvals_count) > 0 ? '#B98900' : '#12161C', marginTop: 3, fontFamily: 'var(--font-mono)' }}>
                {data.status_summary?.AWAITING_APPROVAL ?? data.pending_approvals_count ?? 0}
              </div>
            </div>

            <div style={{ background: '#FFFFFF', padding: '12px 16px', borderRadius: 8, border: '1px solid #D5D8DC' }}>
              <div style={{ fontSize: 11, color: '#8A919B', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>
                In Execution
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#12161C', marginTop: 3, fontFamily: 'var(--font-mono)' }}>
                {data.status_summary?.EXECUTING ?? 0}
              </div>
            </div>

            <div style={{ background: '#FFFFFF', padding: '12px 16px', borderRadius: 8, border: '1px solid #D5D8DC' }}>
              <div style={{ fontSize: 11, color: '#8A919B', textTransform: 'uppercase', fontWeight: 600, letterSpacing: 0.5 }}>
                Resolved & Verified
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: '#1E8E5A', marginTop: 3, fontFamily: 'var(--font-mono)' }}>
                {data.status_summary?.RESOLVED ?? 0}
              </div>
            </div>
          </div>

          {/* 2. CRITICAL DISRUPTION INCIDENTS TABLE (Primary Homepage Section) */}
          <Card style={{ padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 8 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#12161C', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  Critical Disruption Incidents
                </h2>
                <p style={{ margin: '2px 0 0', fontSize: 12, color: '#8A919B' }}>
                  Operational plant disruptions under active autonomous monitoring and mitigation
                </p>
              </div>
              <Button
                onClick={() => navigate('/inbox')}
                variant="secondary"
                style={{ fontSize: 11, padding: '5px 12px' }}
              >
                Communications Inbox →
              </Button>
            </div>

            {(!data.critical_incidents || data.critical_incidents.length === 0) ? (
              <div style={{ textAlign: 'center', padding: 40, color: '#8A919B', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                NO ACTIVE DISRUPTION INCIDENTS DETECTED. ALL PARAMETERS NOMINAL.
              </div>
            ) : (
              <Table>
                <thead>
                  <tr>
                    <Th>Incident ID</Th>
                    <Th>Component</Th>
                    <Th>Disruption Type</Th>
                    <Th>Severity / Risk</Th>
                    <Th>Approval Status</Th>
                    <Th>Current Workflow Stage</Th>
                    <Th>Action</Th>
                  </tr>
                </thead>
                <tbody>
                  {data.critical_incidents.map((inc) => (
                    <tr key={inc.incident_id}>
                      <Td>
                        <code style={{ fontWeight: 700, color: '#003DA5' }}>
                          {inc.incident_id?.slice(0, 16)}
                        </code>
                      </Td>
                      <Td>
                        <div style={{ fontWeight: 600, color: '#12161C', fontSize: 13 }}>
                          {inc.material_name || inc.material_id}
                        </div>
                        {inc.material_name && inc.material_name !== inc.material_id && (
                          <code style={{ fontSize: 11, color: '#8A919B' }}>{inc.material_id}</code>
                        )}
                      </Td>
                      <Td style={{ fontWeight: 500, fontSize: 12, color: '#3A4149', fontFamily: 'var(--font-mono)' }}>
                        {formatDisruptionType(inc.incident_type)}
                      </Td>
                      <Td>
                        <RiskBadge level={inc.severity || 'MEDIUM'} />
                      </Td>
                      <Td>
                        {inc.approval_status === 'PENDING' ? (
                          <span style={{ color: '#B98900', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                            ● SIGN-OFF NEEDED
                          </span>
                        ) : inc.approval_status === 'APPROVED' ? (
                          <span style={{ color: '#1E8E5A', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                            ● AUTHORIZED
                          </span>
                        ) : (
                          <span style={{ color: '#1E8E5A', fontSize: 12, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                            ● AUTO-RESOLVED
                          </span>
                        )}
                      </Td>
                      <Td>
                        <span
                          style={{
                            fontSize: 12,
                            fontWeight: 700,
                            fontFamily: 'var(--font-mono)',
                            color: getStageTextColor(inc.status),
                          }}
                        >
                          ● {inc.status?.replace(/_/g, ' ') || 'DETECTED'}
                        </span>
                      </Td>
                      <Td>
                        <Button
                          onClick={() => navigate(`/incidents/${inc.incident_id}`)}
                          variant="primary"
                          style={{ fontSize: 11, padding: '5px 12px' }}
                        >
                          Review Decision →
                        </Button>
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Card>

          {/* 3. COMPACT "TOP PRODUCTION RISKS" WIDGET (Top 3 Highest-Risk Components) */}
          <Card style={{ padding: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 8 }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#12161C', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                  Top Production Risks
                </h2>
                <p style={{ margin: '2px 0 0', fontSize: 12, color: '#8A919B' }}>
                  Urgent component buffer shortages ranked by hours to line stoppage
                </p>
              </div>
              <button
                onClick={() => navigate('/inventory')}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#003DA5',
                  fontSize: 12,
                  fontWeight: 600,
                  cursor: 'pointer',
                  padding: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 4,
                }}
              >
                View Inventory &rarr;
              </button>
            </div>

            {topProductionRisks.length === 0 ? (
              <div style={{ textAlign: 'center', padding: 24, color: '#8A919B', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
                ALL PRODUCTION BUFFERS WITHIN NOMINAL LIMITS. ZERO IMMEDIATE LINE STOPPAGE RISKS.
              </div>
            ) : (
              <Table>
                <thead>
                  <tr>
                    <Th>Component ID</Th>
                    <Th>Component Name</Th>
                    <Th>Days of Coverage</Th>
                    <Th>Hours to Production Stop</Th>
                    <Th>Risk Level</Th>
                  </tr>
                </thead>
                <tbody>
                  {topProductionRisks.map((item) => (
                    <tr key={item.material_id}>
                      <Td>
                        <code style={{ fontWeight: 700, color: '#003DA5' }}>{item.material_id}</code>
                      </Td>
                      <Td style={{ fontWeight: 600, fontSize: 13, color: '#12161C' }}>
                        {item.material_name}
                      </Td>
                      <Td>
                        <span
                          style={{
                            fontWeight: 700,
                            fontSize: 12,
                            fontFamily: 'var(--font-mono)',
                            color: item.coverage_days < 3 ? '#C4302B' : item.coverage_days < 7 ? '#B98900' : '#1E8E5A',
                          }}
                        >
                          {item.coverage_days}d
                        </span>
                      </Td>
                      <Td>
                        <span
                          style={{
                            fontWeight: 700,
                            fontSize: 12,
                            fontFamily: 'var(--font-mono)',
                            color: item.hours_to_stop < 72 ? '#C4302B' : '#12161C',
                          }}
                        >
                          {item.hours_to_stop}h
                        </span>
                      </Td>
                      <Td>
                        <RiskBadge level={item.risk_level} />
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Card>

        </div>
      ) : null}
    </Layout>
  );
}
