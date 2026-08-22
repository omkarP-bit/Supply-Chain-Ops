import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import Layout from '../components/Layout';
import WorkflowStepper from '../components/WorkflowStepper';
import RiskBadge from '../components/RiskBadge';
import StatusBadge from '../components/StatusBadge';
import { Card, Loading, Error, StatCard, Table, Button } from '../components/UI';

export default function IncidentDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [incident, setIncident] = useState(null);
  const [analysis, setAnalysis] = useState(null);
  const [plans, setPlans] = useState([]);
  const [inventory, setInventory] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [recommending, setRecommending] = useState(false);

  const loadData = () => {
    setLoading(true);
    Promise.all([
      api.getIncident(id),
      api.getPlans(id).catch(() => []),
    ])
      .then(([inc, pl]) => {
        setIncident(inc);
        setPlans(pl);
        if (inc?.workflow_state?.analysis) {
          setAnalysis(inc.workflow_state.analysis);
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [id]);

  useEffect(() => {
    if (incident?.material_id) {
      api.getCoverage(incident.material_id).then(setInventory).catch(() => {});
    }
  }, [incident]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    try {
      const result = await api.analyzeIncident(id);
      setAnalysis(result?.analysis || result);
      loadData();
    } catch (e) {
      alert(e.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleRecommend = async () => {
    setRecommending(true);
    try {
      const result = await api.recommendPlans(id);
      setPlans(result?.plans || result || []);
      loadData();
    } catch (e) {
      alert(e.message);
    } finally {
      setRecommending(false);
    }
  };

  if (loading) return <Layout><Loading /></Layout>;
  if (error) return <Layout><Error message={error} /></Layout>;
  if (!incident) return <Layout><Error message="Incident not found" /></Layout>;

  return (
    <Layout>
      <button
        onClick={() => navigate('/incidents')}
        style={{
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          fontSize: 14,
          color: '#2563eb',
          marginBottom: 12,
          padding: 0,
          fontWeight: 600,
        }}
      >
        &larr; Back to Incidents
      </button>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: '0 0 8px', fontSize: 22, fontWeight: 700, color: '#1e293b' }}>
            Incident <code style={{ fontSize: 16 }}>{incident.incident_id?.slice(0, 8)}</code>
          </h2>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <StatusBadge status={incident.status} />
            <RiskBadge level={incident.severity} />
            <span style={{ fontSize: 13, color: '#64748b' }}>{incident.incident_type?.replace(/_/g, ' ')}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <Button onClick={handleAnalyze} disabled={analyzing} style={{ background: '#2563eb' }}>
            {analyzing ? 'Analyzing Risk...' : '1. Supervisor Risk Analysis'}
          </Button>
          <Button onClick={handleRecommend} disabled={recommending} style={{ background: '#10b981' }}>
            {recommending ? 'Generating Plans...' : '2. Recovery Agent Recommend'}
          </Button>
        </div>
      </div>

      {/* Real-time Multi-Agent Workflow Stepper */}
      <WorkflowStepper currentStep={incident.status} />

      {incident.description && (
        <Card style={{ marginBottom: 16, padding: 16 }}>
          <p style={{ margin: 0, fontSize: 14, color: '#334155' }}>
            <strong>Disruption Overview:</strong> {incident.description}
          </p>
        </Card>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16, marginBottom: 16 }}>
        <Card style={{ padding: 16 }}>
          <h3 style={{ margin: '0 0 10px', fontSize: 14, fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
            Target Component & Affected Entity
          </h3>
          <div style={{ fontSize: 13, lineHeight: 1.8 }}>
            <div><strong>Component ID:</strong> <code>{incident.material_id}</code></div>
            <div><strong>Purchase Order:</strong> <code>{incident.po_id || 'N/A'}</code></div>
            <div><strong>Primary Supplier:</strong> <code>{incident.supplier_id || 'N/A'}</code></div>
          </div>
        </Card>

        {inventory && (
          <Card style={{ padding: 16 }}>
            <h3 style={{ margin: '0 0 10px', fontSize: 14, fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
              Deterministic Inventory Health
            </h3>
            <div style={{ display: 'flex', gap: 16 }}>
              <StatCard label="Days Coverage" value={`${inventory.coverage_days}d`} color={parseFloat(inventory.coverage_days) < 7 ? '#ef4444' : '#10b981'} />
              <StatCard label="Usable Stock" value={inventory.usable_stock} />
              <StatCard label="30d vs 7d Trend" value={inventory.trend_7d_vs_30d?.slice(0, 12)} />
            </div>
          </Card>
        )}
      </div>

      {analysis && (
        <Card style={{ marginBottom: 16, padding: 20 }}>
          <h3 style={{ margin: '0 0 14px', fontSize: 15, fontWeight: 700, color: '#1e293b' }}>
            Deterministic Risk Engine & Hard Filter Results (No LLM)
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12, marginBottom: 16 }}>
            <StatCard label="Risk Level" value={analysis.risk_report?.risk_level} color="#ef4444" />
            <StatCard label="Production Coverage" value={`${analysis.risk_report?.coverage_days}d`} />
            <StatCard label="Hours to Stop" value={analysis.risk_report?.hours_to_production_stop} color="#f59e0b" />
            <StatCard label="Audit Discrepancy" value={`${analysis.risk_report?.discrepancy_percentage}%`} color="#3b82f6" />
          </div>

          <h4 style={{ margin: '14px 0 8px', fontSize: 13, fontWeight: 600, color: '#475569' }}>
            Supplier Candidate Evaluation (Hard Constraint Checked)
          </h4>
          <Table
            columns={[
              { key: 'supplier_id', label: 'Supplier ID' },
              { key: 'supplier_name', label: 'Supplier Name' },
              { key: 'available_quantity', label: 'Stock Available', render: (v) => `${v} units` },
              { key: 'unit_price', label: 'Unit Price', render: (v) => `INR ${v}` },
              { key: 'lead_time_days', label: 'Lead Time', render: (v) => `${v}d` },
              { key: 'certification_valid', label: 'ISO Cert', render: (v) => (v ? '✅ Valid' : '❌ Expired') },
              { key: 'quality_score', label: 'Quality Score' },
              { key: 'score', label: 'Weighted Score', render: (v) => <strong>{v}</strong> },
              { key: 'rejection_reason', label: 'Deterministic Status', render: (v) => v ? <span style={{ color: '#ef4444', fontSize: 12 }}>❌ {v}</span> : <span style={{ color: '#10b981', fontSize: 12 }}>✓ ELIGIBLE</span> },
            ]}
            rows={analysis.eligible_suppliers || []}
          />
        </Card>
      )}

      {plans.length > 0 && (
        <Card style={{ padding: 20 }}>
          <h3 style={{ margin: '0 0 14px', fontSize: 15, fontWeight: 700, color: '#1e293b' }}>
            Recovery Agent Plans & Simulation Stress-Test Results
          </h3>
          <div style={{ display: 'grid', gap: 14 }}>
            {plans.map((plan, i) => (
              <div
                key={plan.plan_id}
                style={{
                  padding: 16,
                  border: `2px solid ${i === 0 ? '#2563eb' : '#e2e8f0'}`,
                  borderRadius: 8,
                  background: i === 0 ? '#eff6ff' : '#ffffff',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexWrap: 'wrap', gap: 8 }}>
                  <div>
                    <strong style={{ fontSize: 15, color: '#0f172a' }}>{plan.plan_name}</strong>
                    <span style={{ marginLeft: 8 }}><StatusBadge status={plan.plan_type} /></span>
                  </div>
                  <div style={{ fontSize: 13, color: '#475569' }}>
                    Robustness & Feasibility Score: <strong style={{ color: '#2563eb', fontSize: 15 }}>{plan.overall_score}</strong>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 20, fontSize: 13, color: '#475569', flexWrap: 'wrap', marginBottom: 8 }}>
                  <span>Estimated Cost: <strong>INR {Number(plan.estimated_cost).toLocaleString()}</strong></span>
                  <span>Delivery: <strong>{plan.estimated_delivery_days} days</strong></span>
                  <span>Production Impact: <strong>{plan.production_impact_hours} hours</strong></span>
                  <StatusBadge status={plan.status} />
                </div>
                {plan.plan_details && (
                  <div style={{ fontSize: 12, color: '#334155', background: '#f8fafc', padding: 10, borderRadius: 6, border: '1px solid #e2e8f0' }}>
                    <strong>Recovery Strategy Rationale:</strong> {plan.plan_details.rationale || plan.plan_details.action || JSON.stringify(plan.plan_details)}
                  </div>
                )}
              </div>
            ))}
          </div>
        </Card>
      )}
    </Layout>
  );
}
