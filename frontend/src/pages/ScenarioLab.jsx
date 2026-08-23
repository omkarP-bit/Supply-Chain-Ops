import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Layout from '../components/Layout';
import { Card, Button, Spinner } from '../components/UI';

const getStatusColor = (status) => {
  if (!status) return '#8A919B';
  const s = status.toUpperCase();
  if (s === 'RESOLVED' || s === 'COMPLETED') return '#1E8E5A';
  if (s === 'AWAITING_APPROVAL' || s === 'AWAITING APPROVAL' || s === 'WAITING_FOR_APPROVAL' || s === 'RUNNING' || s === 'ANALYZING' || s === 'REPLANNING') return '#B98900';
  if (s === 'FAILED' || s === 'CRITICAL') return '#C4302B';
  if (s === 'EXECUTED' || s === 'EXECUTING' || s === 'INJECTED' || s === 'PLAN_READY' || s === 'OPEN') return '#003DA5';
  return '#8A919B';
};

const formatStatusText = (status) => {
  if (!status || status === 'NOT_RUN' || status === 'NOT RUN') return '● NOT RUN';
  if (status === 'AWAITING_APPROVAL') return '● AWAITING APPROVAL';
  if (status === 'RUNNING') return '● RUNNING';
  if (status === 'EXECUTED') return '● EXECUTED';
  return `● ${status.replace(/_/g, ' ')}`;
};

export default function ScenarioLab() {
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [injectingId, setInjectingId] = useState(null);
  const [resettingId, setResettingId] = useState(null);
  const [error, setError] = useState(null);
  const [activeModal, setActiveModal] = useState(null);
  const [expandedDetails, setExpandedDetails] = useState({});

  const navigate = useNavigate();

  const loadScenarios = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.listScenarios();
      setScenarios(data || []);
    } catch (err) {
      setError(err.message || 'Failed to load scenario telemetry');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadScenarios();
  }, []);

  const handleInject = async (scenarioId) => {
    try {
      setInjectingId(scenarioId);
      setError(null);
      const result = await api.injectScenario(scenarioId);
      setActiveModal(result);
      await loadScenarios();
    } catch (err) {
      setError(`Injection failed: ${err.message}`);
    } finally {
      setInjectingId(null);
    }
  };

  const handleReset = async (scenarioId) => {
    try {
      setResettingId(scenarioId);
      setError(null);
      await api.resetScenario(scenarioId);
      await loadScenarios();
    } catch (err) {
      setError(`Reset failed: ${err.message}`);
    } finally {
      setResettingId(null);
    }
  };

  const toggleExpand = (id) => {
    setExpandedDetails((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <Layout>
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#12161C', textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Scenario Lab
          </h1>
          <p style={{ margin: '3px 0 0', color: '#8A919B', fontSize: 13 }}>
            Controlled simulation environment for the six official supply chain disruption scenarios.
          </p>
        </div>
        <Button
          onClick={loadScenarios}
          variant="secondary"
          style={{ fontSize: 12, padding: '7px 12px' }}
        >
          ↻ Refresh State
        </Button>
      </div>

      {/* System Error Alert */}
      {error && (
        <div style={{ padding: 14, background: '#FFFFFF', color: '#C4302B', borderRadius: 6, marginBottom: 20, border: '1px solid #D5D8DC', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          [SCENARIO ENGINE FAULT] {error}
        </div>
      )}

      {/* Injection Feedback Modal */}
      {activeModal && (
        <div style={{
          background: '#FFFFFF',
          border: '1px solid #003DA5',
          borderRadius: 8,
          padding: 18,
          marginBottom: 24,
          boxShadow: '0 4px 12px rgba(0, 61, 165, 0.08)',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid #D5D8DC', paddingBottom: 10, marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: '#003DA5', fontWeight: 900 }}>◈</span>
              <span style={{ fontWeight: 700, fontSize: 14, color: '#12161C' }}>
                Disruption Scenario Injected & Workflow Initiated
              </span>
            </div>
            <button
              onClick={() => setActiveModal(null)}
              style={{ background: 'none', border: 'none', color: '#8A919B', cursor: 'pointer', fontSize: 16 }}
            >
              ✕
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 14, fontFamily: 'var(--font-mono)', fontSize: 12 }}>
            <div>
              <div style={{ color: '#8A919B', fontSize: 11 }}>SCENARIO:</div>
              <div style={{ fontWeight: 700, color: '#12161C' }}>{activeModal.scenario_id} - {activeModal.scenario_name}</div>
            </div>
            <div>
              <div style={{ color: '#8A919B', fontSize: 11 }}>INCIDENT ID:</div>
              <div style={{ fontWeight: 700, color: '#003DA5' }}>{activeModal.incident_id}</div>
            </div>
            <div>
              <div style={{ color: '#8A919B', fontSize: 11 }}>EVENT TYPE:</div>
              <div style={{ fontWeight: 600, color: '#3A4149' }}>{activeModal.event_type}</div>
            </div>
            <div>
              <div style={{ color: '#8A919B', fontSize: 11 }}>WORKFLOW STATUS:</div>
              <div style={{ fontWeight: 700, color: getStatusColor(activeModal.workflow_status) }}>
                {formatStatusText(activeModal.workflow_status)}
              </div>
            </div>
            <div>
              <div style={{ color: '#8A919B', fontSize: 11 }}>PERSISTED TIMESTAMP:</div>
              <div style={{ color: '#3A4149' }}>{new Date(activeModal.timestamp).toLocaleTimeString()}</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
            <Button
              onClick={() => navigate(`/incidents/${activeModal.incident_id}`)}
              variant="primary"
              style={{ fontSize: 12, padding: '7px 16px' }}
            >
              View Real Disruption Dossier &rarr;
            </Button>
            <Button
              onClick={() => setActiveModal(null)}
              variant="secondary"
              style={{ fontSize: 12, padding: '7px 14px' }}
            >
              Close Notification
            </Button>
          </div>
        </div>
      )}

      {/* Scenarios Grid */}
      {loading && scenarios.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#8A919B', fontFamily: 'var(--font-mono)' }}>
          <Spinner size="lg" />
          <div style={{ marginTop: 12, fontSize: 12 }}>LOADING OFFICIAL SCENARIOS...</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 16 }}>
          {scenarios.map((scen, idx) => {
            const isInjecting = injectingId === scen.scenario_id;
            const isResetting = resettingId === scen.scenario_id;
            const isExpanded = !!expandedDetails[scen.scenario_id];

            return (
              <Card key={scen.scenario_id} style={{ padding: 18, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  {/* Top Bar: Number + Status */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: '#003DA5', fontFamily: 'var(--font-mono)' }}>
                      SCENARIO {idx + 1}
                    </span>
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        fontFamily: 'var(--font-mono)',
                        color: getStatusColor(scen.status),
                      }}
                    >
                      {formatStatusText(scen.status)}
                    </span>
                  </div>

                  {/* Scenario Name */}
                  <h3 style={{ margin: '0 0 8px', fontSize: 15, fontWeight: 700, color: '#12161C' }}>
                    {scen.name}
                  </h3>

                  {/* Business Problem */}
                  <p style={{ margin: '0 0 10px', fontSize: 12, color: '#3A4149', lineHeight: 1.4 }}>
                    {scen.business_problem || scen.problem_description}
                  </p>

                  {/* Initial Conditions Injected */}
                  <div style={{ background: '#F4F5F7', padding: '8px 10px', borderRadius: 4, marginBottom: 12, border: '1px solid #D5D8DC', fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                    <div style={{ color: '#8A919B', fontWeight: 600, marginBottom: 2 }}>INITIAL CONDITIONS INJECTED:</div>
                    <div style={{ color: '#12161C', fontWeight: 500 }}>
                      {scen.initial_conditions || `Target: ${scen.target_material} | PO: ${scen.target_po} | Supplier: ${scen.target_supplier}`}
                    </div>
                  </div>

                  {/* Collapsible Details: Expected Agent Behavior */}
                  {isExpanded && (
                    <div style={{ background: '#FFFFFF', padding: 10, borderRadius: 4, marginBottom: 12, fontSize: 12, border: '1px solid #D5D8DC' }}>
                      <div style={{ fontWeight: 600, color: '#12161C', marginBottom: 4 }}>Expected Agent Behavior:</div>
                      <div style={{ color: '#3A4149', marginBottom: 8, lineHeight: 1.4, fontSize: 11 }}>
                        {scen.expected_behavior}
                      </div>

                      <div style={{ fontWeight: 600, color: '#12161C', marginBottom: 4 }}>Key Systems / Engines:</div>
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {scen.systems_involved?.map((sys) => (
                          <span key={sys} style={{ background: '#F4F5F7', border: '1px solid #D5D8DC', padding: '2px 6px', borderRadius: 4, fontSize: 10, fontFamily: 'var(--font-mono)', color: '#3A4149' }}>
                            {sys}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  <button
                    onClick={() => toggleExpand(scen.scenario_id)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#003DA5',
                      fontSize: 11,
                      fontWeight: 600,
                      cursor: 'pointer',
                      padding: 0,
                      marginBottom: 14,
                      display: 'block',
                    }}
                  >
                    {isExpanded ? '▴ Hide Technical Details' : '▾ Show Expected Agent Behavior'}
                  </button>
                </div>

                {/* Bottom Actions */}
                <div style={{ borderTop: '1px solid #D5D8DC', paddingTop: 12, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <Button
                      onClick={() => handleInject(scen.scenario_id)}
                      disabled={isInjecting || isResetting}
                      variant="primary"
                      style={{ fontSize: 11, padding: '6px 12px' }}
                    >
                      {isInjecting ? <Spinner size="sm" /> : null}
                      {isInjecting ? 'Executing Workflow...' : 'Inject Disruption'}
                    </Button>
                    <Button
                      onClick={() => handleReset(scen.scenario_id)}
                      disabled={isInjecting || isResetting}
                      variant="secondary"
                      style={{ fontSize: 11, padding: '6px 10px' }}
                    >
                      {isResetting ? <Spinner size="sm" /> : null}
                      {isResetting ? 'Resetting...' : 'Reset'}
                    </Button>
                  </div>

                  {scen.latest_incident_id && (
                    <Button
                      onClick={() => navigate(`/incidents/${scen.latest_incident_id}`)}
                      variant="secondary"
                      style={{ fontSize: 11, padding: '6px 10px', color: '#003DA5', borderColor: '#003DA5' }}
                    >
                      View Incident &rarr;
                    </Button>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </Layout>
  );
}
