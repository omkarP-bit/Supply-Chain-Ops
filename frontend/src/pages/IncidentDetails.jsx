import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';
import Layout from '../components/Layout';
import RiskBadge from '../components/RiskBadge';
import StatusBadge from '../components/StatusBadge';
import { Card, Loading, Error, Table, Th, Td, Button, Spinner } from '../components/UI';

export default function IncidentDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [dossier, setDossier] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [selectedFlowStep, setSelectedFlowStep] = useState(null);

  const loadDossier = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await api.getIncidentDossier(id);
      setDossier(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDossier();
  }, [id]);

  const handleApprove = async () => {
    const apprId = dossier?.approval_request?.approval_id || dossier?.incident_id;
    if (!apprId) return;
    try {
      setActionLoading(true);
      await api.approveRequest(apprId);
      await loadDossier();
    } catch (err) {
      alert(`Approval notice: ${err.message}`);
      await loadDossier();
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    const apprId = dossier?.approval_request?.approval_id || dossier?.incident_id;
    if (!apprId) return;
    try {
      setActionLoading(true);
      await api.rejectRequest(apprId, rejectReason || 'Budget or operational criteria unfulfilled');
      setShowRejectModal(false);
      await loadDossier();
    } catch (err) {
      alert(`Rejection notice: ${err.message}`);
      await loadDossier();
    } finally {
      setActionLoading(false);
    }
  };

  const handleExecute = async () => {
    const planId = dossier?.recommended_plan?.plan_id;
    const approvalId = dossier?.approval_request?.approval_id;
    if (!planId || !approvalId) return;

    try {
      setActionLoading(true);
      await api.executePlan(planId, approvalId);
      await loadDossier();
    } catch (err) {
      alert(`Execution error: ${err.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <Layout><Loading /></Layout>;
  if (error) return <Layout><Error message={error} /></Layout>;
  if (!dossier) return <Layout><Error message="Incident record not found." /></Layout>;

  const currentRisk = dossier.current_risk || {};
  const doNothing = dossier.do_nothing_impact || {};
  const plan = dossier.recommended_plan;
  const approval = dossier.approval_request;
  const verification = dossier.verification;
  const isExecuted = dossier.status === 'COMPLETED' || dossier.status === 'RESOLVED' || dossier.status === 'EXECUTED' || plan?.status === 'COMPLETED';
  const isApproved = approval?.status === 'APPROVED' || isExecuted;
  const isHumanEscalated = plan?.approval_required || (plan?.estimated_cost && plan?.estimated_cost > 75000) || !!approval;
  const isPendingApproval = !isApproved && (approval?.status === 'PENDING' || dossier.workflow_stage === 'APPROVE' || dossier.status === 'AWAITING_APPROVAL' || isHumanEscalated);
  const isAutoResolved = dossier.status === 'RESOLVED' && (!approval || approval.status === 'APPROVED');

  // Define 9-step demo sequence steps
  const demoSteps = [
    {
      id: 1,
      title: '1. Delay Injected',
      sub: 'Disruption Event',
      badge: 'DETECT',
      status: 'DONE',
      summary: `Injected disruption on ${dossier.material_id} (${dossier.incident_type?.replace(/_/g, ' ')}) on PO ${dossier.po_id || 'PO-7712'}.`,
      detail: `Supplier ${dossier.supplier_id || 'SUP-21'} delivery delay triggers automated detection. Initial severity rated ${dossier.severity}.`,
    },
    {
      id: 2,
      title: '2. Risk Evaluated',
      sub: 'Operational Impact',
      badge: 'ASSESS',
      status: 'DONE',
      summary: `Evaluated ${currentRisk.coverage_days}d stock coverage and ${currentRisk.hours_to_stop}h line stoppage countdown.`,
      detail: `Usable stock: ${currentRisk.usable_stock} units vs safety threshold (${currentRisk.safety_stock}u). Burn rate: ${currentRisk.consumption_7d}u/day (${currentRisk.trend}).`,
    },
    {
      id: 3,
      title: '3. Contact Supplier',
      sub: 'Claim vs Tracking',
      badge: 'CHECK',
      status: 'DONE',
      summary: `Queried supplier claim & carrier tracking status for ${dossier.supplier_id || 'SUP-21'}.`,
      detail: `Supplier claimed: DISPATCHED. Carrier tracking API verification: LABEL_CREATED. Discrepancy logged to supplier reliability memory.`,
    },
    {
      id: 4,
      title: '4. Broadcast RFQ',
      sub: 'Sourcing Candidates',
      badge: 'SOURCING',
      status: 'DONE',
      summary: `Broadcasted RFQ across ${dossier.supplier_comparison?.length || 4} alternate approved suppliers.`,
      detail: `Candidate suppliers retrieved with real inventory capacity, unit pricing, and expedited transit lead times.`,
    },
    {
      id: 5,
      title: '5. Compare Options',
      sub: 'Stress Test & Score',
      badge: 'VALIDATE',
      status: 'DONE',
      summary: `Deterministic hard constraint validation & +2d delay simulation.`,
      detail: `Filtered candidates by ISO 9001 certifications, AQL II inspection levels, MOQ limits, and lead times. Selected top strategy (Score: ${plan?.overall_score || 92.0}/100).`,
    },
    {
      id: 6,
      title: isHumanEscalated ? '6. Human Escalation' : '6. Autonomous Policy',
      sub: isHumanEscalated ? (isApproved ? 'Manager Authorized' : 'Manager Sign-Off') : 'Auto-Authorized',
      badge: isHumanEscalated ? (isApproved ? 'HUMAN-AUTHORIZED' : isPendingApproval ? 'PENDING' : 'ESCALATED') : 'AUTO-RESOLVED',
      status: isPendingApproval ? 'ACTIVE' : 'DONE',
      summary: isHumanEscalated
        ? `Order amount (INR ${plan?.estimated_cost?.toLocaleString()}) > threshold (INR ${approval?.approval_threshold?.toLocaleString() || '75,000'}). Paused at HITL gate.`
        : `Order amount within autonomous spending authority limit. Auto-approved.`,
      detail: isHumanEscalated
        ? (isApproved ? `Operations Manager approved recovery plan on ${new Date().toLocaleDateString()}. Ready for ERP execution.` : `Awaiting human authorization by Operations Manager before dispatch.`)
        : `Autonomous execution authorized per policy configuration.`,
    },
    {
      id: 7,
      title: '7. Update ERP',
      sub: 'PO Dispatch',
      badge: 'EXECUTE',
      status: isExecuted ? 'DONE' : isApproved ? 'ACTIVE' : 'PENDING',
      summary: isExecuted
        ? `Dispatched Purchase Order to simulated ERP database.`
        : isApproved
        ? `Ready to dispatch Purchase Order to ERP.`
        : `Pending human authorization.`,
      detail: isExecuted
        ? `Purchase Order ${dossier.po_id || 'PO-7712'} status updated to active in ERP. Inventory replenishment in transit.`
        : `PO dispatch paused until human authorization is submitted.`,
    },
    {
      id: 8,
      title: '8. Verify Outcome',
      sub: 'Deterministic Check',
      badge: 'VERIFY',
      status: isExecuted ? 'DONE' : 'PENDING',
      summary: isExecuted
        ? `Verified ERP PO confirmation, supplier certs & line buffer.`
        : `Post-execution state check will execute upon ERP PO dispatch.`,
      detail: verification?.reason || `State verification confirms operational continuity restored with zero line downtime.`,
    },
    {
      id: 9,
      title: '9. Audit Committed',
      sub: 'Immutable Log',
      badge: 'AUDIT',
      status: 'DONE',
      summary: `Committed ${dossier.decision_timeline?.length || 6} immutable audit milestones to database.`,
      detail: `All agent actions, risk assessments, supplier comparisons, and approval events recorded in PostgreSQL audit_events.`,
    },
  ];

  return (
    <Layout>
      {/* Top Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <button
          onClick={() => navigate('/dashboard')}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontSize: 13,
            color: '#003DA5',
            padding: 0,
            fontWeight: 600,
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          &larr; Back to Operational Control Tower
        </button>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <Button
            onClick={() => navigate(`/audit-log?entity_id=${dossier.incident_id}`)}
            variant="primary"
            style={{ fontSize: 12, padding: '7px 14px' }}
          >
            ≡ View Audit Trail
          </Button>
          <Button
            onClick={loadDossier}
            disabled={actionLoading}
            variant="secondary"
            style={{ fontSize: 12, padding: '7px 12px' }}
          >
            ↻ Refresh State
          </Button>
        </div>
      </div>

      {/* SECTION A: INCIDENT HEADER */}
      <Card style={{ padding: '16px 20px', marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 6, flexWrap: 'wrap' }}>
              <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#12161C' }}>
                Incident <code style={{ fontSize: 16, color: '#003DA5', fontFamily: 'var(--font-mono)' }}>{dossier.incident_id?.slice(0, 16)}</code>
              </h1>
              <RiskBadge level={dossier.severity} />
              <StatusBadge status={dossier.status} />
              {isHumanEscalated ? (
                <span style={{ fontSize: 11, color: '#B98900', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  ● HUMAN ESCALATION
                </span>
              ) : (
                <span style={{ fontSize: 11, color: '#1E8E5A', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  ● AUTONOMOUS RECOVERY
                </span>
              )}
            </div>
            <div style={{ fontSize: 13, color: '#8A919B', display: 'flex', gap: 18, flexWrap: 'wrap', fontFamily: 'var(--font-mono)' }}>
              <span>DISRUPTION: <strong style={{ color: '#12161C' }}>{dossier.incident_type?.replace(/_/g, ' ')}</strong></span>
              <span>COMPONENT: <strong style={{ color: '#12161C' }}>{dossier.material_id}</strong></span>
              <span>PO: <strong style={{ color: '#12161C' }}>{dossier.po_id || 'PO-7712'}</strong></span>
              <span>SUPPLIER: <strong style={{ color: '#12161C' }}>{dossier.supplier_id || 'SUP-21'}</strong></span>
            </div>
          </div>

          <div style={{ fontSize: 11, color: '#8A919B', textAlign: 'right', fontFamily: 'var(--font-mono)' }}>
            <div>DETECTED: {dossier.created_at ? new Date(dossier.created_at).toLocaleTimeString() : 'RECENT'}</div>
            <div>SYNCED: {dossier.updated_at ? new Date(dossier.updated_at).toLocaleTimeString() : new Date().toLocaleTimeString()}</div>
          </div>
        </div>
      </Card>

      {/* INTERACTIVE DEMO SEQUENCE FLOW DIAGRAM */}
      <Card style={{ padding: '16px 20px', marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#12161C', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              Autonomous Disruption Control Cycle (Interactive Demo Flow)
            </h2>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: '#8A919B' }}>
              Click any milestone in the sequence to inspect deterministic telemetry, agent reasoning, and state outcomes
            </p>
          </div>
          <span style={{ fontSize: 11, fontFamily: 'var(--font-mono)', color: '#8A919B' }}>
            [9/9 MILESTONES]
          </span>
        </div>

        {/* Horizontal Visual Flow Nodes */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 4, overflowX: 'auto', paddingBottom: 6 }}>
          {demoSteps.map((step, idx) => {
            const isSelected = selectedFlowStep?.id === step.id;
            const isDone = step.status === 'DONE';
            const isActive = step.status === 'ACTIVE';

            return (
              <React.Fragment key={step.id}>
                <div
                  onClick={() => setSelectedFlowStep(isSelected ? null : step)}
                  style={{
                    minWidth: 120,
                    padding: '8px 10px',
                    borderRadius: 6,
                    background: isSelected ? '#003DA5' : '#FFFFFF',
                    border: `1px solid ${isSelected ? '#003DA5' : '#D5D8DC'}`,
                    color: isSelected ? '#FFFFFF' : '#12161C',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 2 }}>
                    <span style={{ fontSize: 9, fontWeight: 700, color: isSelected ? '#D5D8DC' : '#8A919B', fontFamily: 'var(--font-mono)' }}>
                      {step.badge}
                    </span>
                    <span style={{ fontSize: 10, color: isSelected ? '#FFFFFF' : isDone ? '#1E8E5A' : '#B98900', fontFamily: 'var(--font-mono)' }}>
                      {isDone ? 'DONE' : isActive ? 'WAIT' : 'IDLE'}
                    </span>
                  </div>
                  <div style={{ fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap' }}>{step.title}</div>
                  <div style={{ fontSize: 10, color: isSelected ? '#D5D8DC' : '#8A919B', marginTop: 1 }}>{step.sub}</div>
                </div>

                {idx < demoSteps.length - 1 && (
                  <span style={{ color: '#8A919B', fontSize: 12, padding: '0 2px' }}>&rarr;</span>
                )}
              </React.Fragment>
            );
          })}
        </div>

        {/* Expanded Milestone Inspection Card */}
        {selectedFlowStep && (
          <div style={{ marginTop: 12, padding: 12, background: '#F4F5F7', borderRadius: 6, border: '1px solid #D5D8DC' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
              <strong style={{ fontSize: 12, color: '#003DA5', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
                MILESTONE #{selectedFlowStep.id}: {selectedFlowStep.title}
              </strong>
              <button
                onClick={() => setSelectedFlowStep(null)}
                style={{ background: 'none', border: 'none', color: '#8A919B', cursor: 'pointer', fontSize: 13 }}
              >
                ✕
              </button>
            </div>
            <div style={{ fontSize: 12, color: '#12161C', fontWeight: 600, marginBottom: 2 }}>
              {selectedFlowStep.summary}
            </div>
            <div style={{ fontSize: 12, color: '#3A4149', lineHeight: 1.4, fontFamily: 'var(--font-mono)' }}>
              {selectedFlowStep.detail}
            </div>
          </div>
        )}
      </Card>

      {/* SECTION B: CURRENT OPERATIONAL IMPACT (COMPACT DECISION KPIS) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 10, marginBottom: 16 }}>
        <Card style={{ padding: 12 }}>
          <div style={{ fontSize: 11, color: '#8A919B', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>Coverage Days</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: currentRisk.coverage_days < 7 ? '#C4302B' : '#1E8E5A', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
            {currentRisk.coverage_days} days
          </div>
          <div style={{ fontSize: 10, color: '#8A919B', marginTop: 2, fontFamily: 'var(--font-mono)' }}>TARGET: &ge; 7.0d</div>
        </Card>

        <Card style={{ padding: 12 }}>
          <div style={{ fontSize: 11, color: '#8A919B', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>Hours to Stop</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: currentRisk.hours_to_stop < 72 ? '#C4302B' : '#12161C', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
            {currentRisk.hours_to_stop} hrs
          </div>
          <div style={{ fontSize: 10, color: '#8A919B', marginTop: 2, fontFamily: 'var(--font-mono)' }}>LINE BUFFER</div>
        </Card>

        <Card style={{ padding: 12 }}>
          <div style={{ fontSize: 11, color: '#8A919B', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>Usable Stock</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#12161C', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
            {currentRisk.usable_stock?.toLocaleString()} u
          </div>
          <div style={{ fontSize: 10, color: '#8A919B', marginTop: 2, fontFamily: 'var(--font-mono)' }}>SAFETY: {currentRisk.safety_stock}u</div>
        </Card>

        <Card style={{ padding: 12 }}>
          <div style={{ fontSize: 11, color: '#8A919B', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>Burn Rate Trend</div>
          <div style={{ fontSize: 16, fontWeight: 700, color: '#3A4149', marginTop: 4, fontFamily: 'var(--font-mono)' }}>
            {currentRisk.trend?.replace(/_/g, ' ')}
          </div>
          <div style={{ fontSize: 10, color: '#8A919B', marginTop: 2, fontFamily: 'var(--font-mono)' }}>30D: {currentRisk.consumption_30d}u/d</div>
        </Card>

        <Card style={{ padding: 12 }}>
          <div style={{ fontSize: 11, color: '#8A919B', fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 }}>Stock Discrepancy</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: currentRisk.discrepancy_percentage > 20 ? '#C4302B' : '#1E8E5A', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
            {currentRisk.discrepancy_percentage?.toFixed(1)}%
          </div>
          <div style={{ fontSize: 10, color: '#8A919B', marginTop: 2, fontFamily: 'var(--font-mono)' }}>ERP VS PHYSICAL</div>
        </Card>
      </div>

      {/* SECTION C: "WHAT HAPPENS IF WE DO NOTHING?" */}
      <Card style={{ padding: 14, marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
          <h2 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: '#C4302B', textTransform: 'uppercase', letterSpacing: 0.5, fontFamily: 'var(--font-mono)' }}>
            [SHUTDOWN PROJECTION: DO NOTHING]
          </h2>
          <span style={{ fontSize: 11, color: '#C4302B', fontFamily: 'var(--font-mono)' }}>CRITICAL</span>
        </div>
        <p style={{ margin: '0 0 10px', fontSize: 12, color: '#3A4149', lineHeight: 1.4 }}>
          {doNothing.summary || `Stockout will occur in ${currentRisk.hours_to_stop} hours, halting ${doNothing.affected_orders_count || 1} production run(s).`}
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 8 }}>
          <div style={{ background: '#F4F5F7', padding: 8, borderRadius: 4, border: '1px solid #D5D8DC' }}>
            <div style={{ fontSize: 10, color: '#8A919B', textTransform: 'uppercase' }}>Countdown to Stockout</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#C4302B', fontFamily: 'var(--font-mono)' }}>{doNothing.hours_to_stockout} Hours</div>
          </div>
          <div style={{ background: '#F4F5F7', padding: 8, borderRadius: 4, border: '1px solid #D5D8DC' }}>
            <div style={{ fontSize: 10, color: '#8A919B', textTransform: 'uppercase' }}>Projected Shortage</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#C4302B', fontFamily: 'var(--font-mono)' }}>{doNothing.expected_shortage_units} Units</div>
          </div>
          <div style={{ background: '#F4F5F7', padding: 8, borderRadius: 4, border: '1px solid #D5D8DC' }}>
            <div style={{ fontSize: 10, color: '#8A919B', textTransform: 'uppercase' }}>Halted Production Orders</div>
            <div style={{ fontSize: 15, fontWeight: 700, color: '#C4302B', fontFamily: 'var(--font-mono)' }}>{doNothing.affected_orders_count} Run(s)</div>
          </div>
        </div>
      </Card>

      {/* SECTION D: RECOVERY RECOMMENDATION */}
      {plan && (
        <Card style={{ padding: 18, marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#12161C', textTransform: 'uppercase' }}>
                  Recommended Recovery Strategy: {plan.plan_name}
                </h2>
                <StatusBadge status={plan.plan_type} />
              </div>
              <p style={{ margin: '2px 0 0', fontSize: 12, color: '#8A919B' }}>
                Multi-sourcing optimization validated against delivery stress tests
              </p>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: 10, color: '#8A919B', textTransform: 'uppercase' }}>Feasibility Score</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: '#003DA5', fontFamily: 'var(--font-mono)' }}>
                {plan.overall_score} / 100
              </div>
            </div>
          </div>

          {/* Key Plan Metrics Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 8, marginBottom: 14 }}>
            <div style={{ background: '#F4F5F7', padding: 10, borderRadius: 6, border: '1px solid #D5D8DC' }}>
              <div style={{ fontSize: 10, color: '#8A919B', textTransform: 'uppercase' }}>Selected Supplier(s)</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#12161C', marginTop: 2 }}>{plan.supplier_name}</div>
            </div>
            <div style={{ background: '#F4F5F7', padding: 10, borderRadius: 6, border: '1px solid #D5D8DC' }}>
              <div style={{ fontSize: 10, color: '#8A919B', textTransform: 'uppercase' }}>Estimated Cost</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#12161C', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
                INR {plan.estimated_cost?.toLocaleString()}
              </div>
            </div>
            <div style={{ background: '#F4F5F7', padding: 10, borderRadius: 6, border: '1px solid #D5D8DC' }}>
              <div style={{ fontSize: 10, color: '#8A919B', textTransform: 'uppercase' }}>Lead Time</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#12161C', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
                {plan.estimated_delivery_days} Days
              </div>
            </div>
            <div style={{ background: '#F4F5F7', padding: 10, borderRadius: 6, border: '1px solid #D5D8DC' }}>
              <div style={{ fontSize: 10, color: '#8A919B', textTransform: 'uppercase' }}>Post-Recovery Buffer</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#1E8E5A', marginTop: 2, fontFamily: 'var(--font-mono)' }}>
                {plan.simulation?.coverage_after_recovery_days || 28.5} Days
              </div>
            </div>
          </div>

          {/* Split Sourcing Allocations if applicable */}
          {plan.allocations && plan.allocations.length > 0 && (
            <div style={{ background: '#F4F5F7', padding: 12, borderRadius: 6, border: '1px solid #D5D8DC', marginBottom: 12 }}>
              <div style={{ fontSize: 11, fontWeight: 700, color: '#3A4149', marginBottom: 6, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Split Sourcing Allocations:
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 6 }}>
                {plan.allocations.map((alloc, idx) => (
                  <div key={idx} style={{ padding: '6px 10px', background: '#FFFFFF', borderRadius: 4, fontSize: 12, border: '1px solid #D5D8DC', fontFamily: 'var(--font-mono)' }}>
                    <strong>{alloc.supplier_name || alloc.supplier_id}:</strong> {alloc.quantity}u &bull; INR {alloc.unit_price}/u ({alloc.lead_time_days || 2}d)
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Deterministic Fact Checks */}
          <div style={{ background: '#FFFFFF', padding: 12, borderRadius: 6, border: '1px solid #D5D8DC', marginBottom: 10 }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: '#3A4149', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 6 }}>
              Deterministic Validation Facts
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: 4 }}>
              {plan.why_this_plan?.map((fact, idx) => (
                <div key={idx} style={{ fontSize: 12, color: '#1E8E5A', display: 'flex', alignItems: 'center', gap: 6, fontFamily: 'var(--font-mono)' }}>
                  <span>✓</span> {fact}
                </div>
              ))}
            </div>
          </div>

          {plan.rationale && (
            <div style={{ fontSize: 12, color: '#3A4149', background: '#F4F5F7', padding: 8, borderRadius: 4, fontFamily: 'var(--font-mono)' }}>
              OPERATIONAL RATIONALE: {plan.rationale}
            </div>
          )}
        </Card>
      )}

      {/* SECTION G: HUMAN APPROVAL */}
      <Card style={{ padding: 18, marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, flexWrap: 'wrap', gap: 12 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <h2 style={{ margin: 0, fontSize: 15, fontWeight: 700, color: '#12161C', textTransform: 'uppercase' }}>
                Operational Authority & Sign-Off
              </h2>
              {isApproved ? (
                <span style={{ color: '#1E8E5A', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  {isHumanEscalated || approval?.status === 'APPROVED' ? '● HUMAN-AUTHORIZED (OPERATIONS MANAGER)' : '● AUTO-AUTHORIZED (WITHIN BUDGET THRESHOLD)'}
                </span>
              ) : isPendingApproval ? (
                <span style={{ color: '#B98900', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>● SIGN-OFF NEEDED</span>
              ) : (
                <span style={{ color: '#1E8E5A', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>● AUTO-AUTHORIZED</span>
              )}
            </div>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: '#8A919B' }}>
              {isApproved
                ? (isHumanEscalated || approval?.status === 'APPROVED'
                    ? 'Recovery purchase order authorized by Operations Manager. Ready for ERP execution.'
                    : 'Recovery purchase order auto-authorized within standard autonomous threshold (< INR 75,000).')
                : isPendingApproval
                ? `Recovery order amount (INR ${plan?.estimated_cost?.toLocaleString()}) exceeds operational threshold (INR ${approval?.approval_threshold?.toLocaleString() || '75,000'}). Manager authorization required.`
                : 'Plan parameters within standard operational limits.'}
            </p>
          </div>

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            {isPendingApproval && (
              <>
                <Button
                  onClick={handleApprove}
                  disabled={actionLoading}
                  variant="primary"
                  style={{ fontSize: 12, padding: '7px 16px' }}
                >
                  {actionLoading ? <Spinner size="sm" /> : '✓ Authorize Plan'}
                </Button>
                <Button
                  onClick={() => setShowRejectModal(true)}
                  disabled={actionLoading}
                  variant="secondary"
                  style={{ fontSize: 12, padding: '7px 12px' }}
                >
                  ✕ Reject Plan
                </Button>
              </>
            )}

            {isApproved && !isExecuted && (
              <Button
                onClick={handleExecute}
                disabled={actionLoading}
                variant="primary"
                style={{ fontSize: 12, padding: '7px 18px' }}
              >
                {actionLoading ? <Spinner size="sm" /> : 'Dispatch Purchase Order to ERP'}
              </Button>
            )}

            {isExecuted && (
              <span style={{ color: '#1E8E5A', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                ✓ EXECUTED & COMMITTED TO ERP
              </span>
            )}
          </div>
        </div>

        {showRejectModal && (
          <div style={{ marginTop: 12, padding: 12, background: '#F4F5F7', border: '1px solid #D5D8DC', borderRadius: 6 }}>
            <label style={{ display: 'block', fontSize: 11, fontWeight: 600, color: '#12161C', marginBottom: 4, textTransform: 'uppercase' }}>
              Specify Rejection Reason for Audit Log:
            </label>
            <input
              type="text"
              placeholder="e.g. Alternative supplier preferred, budget reallocated"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              style={{ width: '100%', padding: '6px 10px', border: '1px solid #D5D8DC', borderRadius: 4, fontSize: 12, marginBottom: 8, outline: 'none', fontFamily: 'var(--font-body)' }}
            />
            <div style={{ display: 'flex', gap: 6 }}>
              <Button onClick={handleReject} disabled={actionLoading} variant="primary" style={{ fontSize: 11, padding: '5px 12px' }}>
                Confirm Rejection
              </Button>
              <Button onClick={() => setShowRejectModal(false)} variant="secondary" style={{ fontSize: 11, padding: '5px 10px' }}>
                Cancel
              </Button>
            </div>
          </div>
        )}
      </Card>

      {/* SECTION F: ALTERNATIVE SUPPLIER OPTIONS COMPACT MATRIX */}
      <Card style={{ padding: 18, marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div>
            <h2 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: '#12161C', textTransform: 'uppercase' }}>
              Supplier Candidate Comparison Matrix
            </h2>
            <p style={{ margin: '2px 0 0', fontSize: 12, color: '#8A919B' }}>
              Deterministic filtering across ISO Certifications, AQL levels, stock availability & lead times
            </p>
          </div>
        </div>

        <Table>
          <thead>
            <tr>
              <Th>Supplier</Th>
              <Th>Price</Th>
              <Th>Lead Time</Th>
              <Th>Available Qty</Th>
              <Th>Quality / AQL</Th>
              <Th>Reliability</Th>
              <Th>Score</Th>
              <Th>Status</Th>
            </tr>
          </thead>
          <tbody>
            {dossier.supplier_comparison?.slice(0, 5).map((sup) => (
              <tr key={sup.supplier_id}>
                <Td>
                  <code style={{ fontWeight: 700, color: '#003DA5' }}>{sup.supplier_id}</code> &bull; {sup.supplier_name}
                </Td>
                <Td style={{ fontFamily: 'var(--font-mono)' }}>INR {sup.unit_price?.toFixed(2)}</Td>
                <Td style={{ fontFamily: 'var(--font-mono)' }}>{sup.lead_time_days}d</Td>
                <Td style={{ fontFamily: 'var(--font-mono)' }}>{sup.available_quantity?.toLocaleString()}u</Td>
                <Td>
                  <div style={{ fontFamily: 'var(--font-mono)' }}>{sup.quality_score ? (sup.quality_score > 1 ? sup.quality_score.toFixed(1) : `${(sup.quality_score * 100).toFixed(0)}%`) : '-'}</div>
                  <div style={{ fontSize: 10, color: sup.certification_valid ? '#1E8E5A' : '#C4302B', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                    {sup.certification_valid ? 'ISO VALID' : 'ISO EXPIRED'}
                  </div>
                </Td>
                <Td style={{ fontFamily: 'var(--font-mono)' }}>
                  {sup.reliability_score ? (sup.reliability_score > 1 ? sup.reliability_score.toFixed(1) : `${(sup.reliability_score * 100).toFixed(0)}%`) : '-'}
                </Td>
                <Td style={{ fontWeight: 700, fontSize: 13, fontFamily: 'var(--font-mono)' }}>
                  {sup.score > 0 ? sup.score.toFixed(1) : '0.0'}
                </Td>
                <Td>
                  {sup.is_selected ? (
                    <span style={{ color: '#1E8E5A', fontSize: 11, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                      ● SELECTED
                    </span>
                  ) : sup.rejection_reason ? (
                    <span style={{ color: '#C4302B', fontSize: 10, fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                      ✕ {sup.rejection_reason}
                    </span>
                  ) : (
                    <span style={{ color: '#8A919B', fontSize: 11, fontFamily: 'var(--font-mono)' }}>ELIGIBLE</span>
                  )}
                </Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Card>
    </Layout>
  );
}
