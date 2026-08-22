import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import Layout from '../components/Layout';
import RiskBadge from '../components/RiskBadge';
import StatusBadge from '../components/StatusBadge';
import { Card, Loading, Error, StatCard, Table } from '../components/UI';

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

  useEffect(() => {
    setLoading(true);
    Promise.all([
      api.getIncident(id),
      api.getPlans(id).catch(() => []),
    ])
      .then(([inc, pl]) => { setIncident(inc); setPlans(pl); })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
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
      setAnalysis(result);
    } catch (e) { alert(e.message); }
    setAnalyzing(false);
  };

  const handleRecommend = async () => {
    setRecommending(true);
    try {
      const result = await api.recommendPlans(id);
      setPlans(result);
    } catch (e) { alert(e.message); }
    setRecommending(false);
  };

  if (loading) return <Layout><Loading /></Layout>;
  if (error) return <Layout><Error message={error} /></Layout>;
  if (!incident) return <Layout><Error message="Incident not found" /></Layout>;

  return (
    <Layout>
      <button onClick={() => navigate('/incidents')} style={{
        background: 'none', border: 'none', cursor: 'pointer', fontSize: 14,
        color: '#1565c0', marginBottom: 12, padding: 0,
      }}>&larr; Back to Incidents</button>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 }}>
        <div>
          <h2 style={{ margin: '0 0 8px', fontSize: 22, fontWeight: 700, color: '#1a1a2e' }}>
            Incident <code style={{ fontSize: 16 }}>{incident.incident_id?.slice(0, 8)}</code>
          </h2>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <StatusBadge status={incident.status} />
            <RiskBadge level={incident.severity} />
            <span style={{ fontSize: 13, color: '#666' }}>{incident.incident_type?.replace(/_/g, ' ')}</span>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={handleAnalyze} disabled={analyzing} style={{
            padding: '8px 16px', borderRadius: 6, border: '1px solid #1565c0', background: '#1565c0',
            color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer',
          }}>{analyzing ? 'Analyzing...' : 'Analyze Risk'}</button>
          <button onClick={handleRecommend} disabled={recommending} style={{
            padding: '8px 16px', borderRadius: 6, border: '1px solid #2e7d32', background: '#2e7d32',
            color: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer',
          }}>{recommending ? 'Generating...' : 'Get Recommendations'}</button>
        </div>
      </div>

      {incident.description && (
        <Card style={{ marginBottom: 16 }}>
          <p style={{ margin: 0, fontSize: 14, color: '#444' }}>{incident.description}</p>
        </Card>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 16 }}>
        <Card>
          <h3 style={{ margin: '0 0 10px', fontSize: 14, fontWeight: 600, color: '#555' }}>Material</h3>
          <div style={{ fontSize: 13 }}>
            <div><strong>ID:</strong> {incident.material_id}</div>
            <div><strong>PO:</strong> {incident.po_id || '-'}</div>
            <div><strong>Supplier:</strong> {incident.supplier_id || '-'}</div>
          </div>
        </Card>

        {inventory && (
          <Card>
            <h3 style={{ margin: '0 0 10px', fontSize: 14, fontWeight: 600, color: '#555' }}>Inventory Coverage</h3>
            <div style={{ display: 'flex', gap: 16 }}>
              <StatCard label="Coverage" value={`${inventory.coverage_days}d`} color={parseFloat(inventory.coverage_days) < 7 ? '#c62828' : '#2e7d32'} />
              <StatCard label="Usable Stock" value={inventory.usable_stock} />
              <StatCard label="Trend" value={inventory.trend_7d_vs_30d?.slice(0, 10)} />
            </div>
          </Card>
        )}
      </div>

      {analysis && (
        <Card style={{ marginBottom: 16 }}>
          <h3 style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 600 }}>Risk Analysis</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: 12, marginBottom: 16 }}>
            <StatCard label="Risk Level" value={analysis.risk_report?.risk_level} color="#c62828" />
            <StatCard label="Coverage" value={`${analysis.risk_report?.coverage_days}d`} />
            <StatCard label="Hours to Stop" value={analysis.risk_report?.hours_to_production_stop} color="#e65100" />
            <StatCard label="Discrepancy" value={`${analysis.risk_report?.discrepancy_percentage}%`} color="#f57f17" />
          </div>

          <h4 style={{ margin: '0 0 8px', fontSize: 13, fontWeight: 600, color: '#555' }}>Eligible Suppliers</h4>
          <Table
            columns={[
              { key: 'supplier_id', label: 'ID' },
              { key: 'supplier_name', label: 'Name' },
              { key: 'available_quantity', label: 'Stock', render: (v) => `${v} units` },
              { key: 'unit_price', label: 'Price', render: (v) => `₹${v}` },
              { key: 'lead_time_days', label: 'Lead Time', render: (v) => `${v}d` },
              { key: 'certification_valid', label: 'Cert', render: (v) => v ? '✅' : '❌' },
              { key: 'quality_score', label: 'Quality' },
              { key: 'score', label: 'Score', render: (v) => <strong>{v}</strong> },
              { key: 'rejection_reason', label: 'Rejection', render: (v) => v ? <span style={{ color: '#c62828', fontSize: 12 }}>{v}</span> : '-' },
            ]}
            rows={analysis.eligible_suppliers || []}
          />
        </Card>
      )}

      {plans.length > 0 && (
        <Card>
          <h3 style={{ margin: '0 0 12px', fontSize: 15, fontWeight: 600 }}>Recovery Plans</h3>
          <div style={{ display: 'grid', gap: 12 }}>
            {plans.map((plan, i) => (
              <div key={plan.plan_id} style={{
                padding: 16, border: `2px solid ${i === 0 ? '#1565c0' : '#e0e0e0'}`,
                borderRadius: 8, background: i === 0 ? '#f0f7ff' : '#fff',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                  <div>
                    <strong style={{ fontSize: 14 }}>{plan.plan_name}</strong>
                    <StatusBadge status={plan.plan_type} />
                  </div>
                  <div style={{ fontSize: 13, color: '#666' }}>
                    Score: <strong>{plan.overall_score}</strong>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 20, fontSize: 13, color: '#555' }}>
                  <span>Cost: <strong>₹{Number(plan.estimated_cost).toLocaleString()}</strong></span>
                  <span>Delivery: <strong>{plan.estimated_delivery_days}d</strong></span>
                  <span>Production Impact: <strong>{plan.production_impact_hours}h</strong></span>
                  <StatusBadge status={plan.status} />
                </div>
                {plan.plan_details && (
                  <div style={{ marginTop: 8, fontSize: 12, color: '#666', background: '#f8f9fa', padding: 8, borderRadius: 4 }}>
                    {plan.plan_details.rationale || plan.plan_details.action || JSON.stringify(plan.plan_details)}
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
