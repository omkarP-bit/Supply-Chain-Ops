import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import Layout from '../components/Layout';
import { Card, Button, Badge, RiskBadge, Loading, Table, Th, Td, Modal, Input, Spinner } from '../components/UI';
import { api } from '../services/api';

export default function IncidentDetails() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [dossier, setDossier] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [selectedPlanId, setSelectedPlanId] = useState(null);
  const [activeTab, setActiveTab] = useState('demo_flow'); // 'demo_flow' | 'mvp_suite'

  const loadDossier = async () => {
    try {
      const data = await api.getIncidentDossier(id);
      setDossier(data);
      if (data?.recommended_plan?.plan_id && !selectedPlanId) {
        setSelectedPlanId(data.recommended_plan.plan_id);
      }
    } catch (err) {
      console.error('Failed to load incident dossier:', err);
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
    const planId = dossier?.recommended_plan?.plan_id || selectedPlanId;
    const approvalId = dossier?.approval_request?.approval_id || dossier?.incident_id;
    if (!planId || !approvalId) return;

    try {
      setActionLoading(true);
      await api.executePlan(planId, approvalId);
      await loadDossier();
    } catch (err) {
      alert(`Execution notice: ${err.message}`);
      await loadDossier();
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <Layout><Loading /></Layout>;

  if (!dossier) {
    return (
      <Layout>
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 20px' }}>
            <h2 style={{ color: '#12161C', marginBottom: 8, fontSize: 20 }}>Disruption Report Not Found</h2>
            <p style={{ color: '#8A919B', marginBottom: 20, fontSize: 14 }}>Could not load operational data for incident {id}.</p>
            <Button onClick={() => navigate('/')} variant="primary">Return to Homepage</Button>
          </div>
        </Card>
      </Layout>
    );
  }

  const currentRisk = dossier.current_risk || {};
  const doNothing = dossier.do_nothing_impact || {};
  const plan = dossier.recommended_plan;
  const approval = dossier.approval_request;
  const demoSteps = dossier.demo_flow_steps || [];
  const mvp = dossier.mvp_features || {};

  const isExecuted = dossier.status === 'COMPLETED' || dossier.status === 'RESOLVED' || dossier.status === 'EXECUTED' || plan?.status === 'COMPLETED';
  const isApproved = approval?.status === 'APPROVED' || dossier.status === 'APPROVED' || isExecuted;
  const isHumanEscalated = plan?.approval_required || (plan?.estimated_cost && plan?.estimated_cost > 75000) || !!approval;
  const isPendingApproval = !isApproved && (approval?.status === 'PENDING' || dossier.workflow_stage === 'APPROVE' || dossier.status === 'AWAITING_APPROVAL' || isHumanEscalated);

  const getStageTextColor = (status) => {
    switch (status) {
      case 'RESOLVED':
      case 'COMPLETED':
        return '#1E8E5A';
      case 'APPROVED':
      case 'EXECUTING':
        return '#003DA5';
      case 'AWAITING_APPROVAL':
      case 'ANALYZING':
      case 'REPLANNING':
        return '#B98900';
      default:
        return '#C4302B';
    }
  };

  return (
    <Layout>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20, maxWidth: 1200, margin: '0 auto', paddingBottom: 40 }}>
        
        {/* Navigation Breadcrumb */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, color: '#8A919B' }}>
            <Link to="/" style={{ color: '#003DA5', textDecoration: 'none', fontWeight: 600 }}>Homepage</Link>
            <span>/</span>
            <Link to="/scenario-lab" style={{ color: '#003DA5', textDecoration: 'none', fontWeight: 600 }}>Scenario Lab</Link>
            <span>/</span>
            <span style={{ color: '#12161C', fontWeight: 600 }}>Disruption Dossier {dossier.incident_id}</span>
          </div>

          <div style={{ display: 'flex', gap: 8 }}>
            <Button onClick={() => navigate('/scenario-lab')} variant="secondary" style={{ fontSize: 13 }}>
              ◈ Scenario Lab
            </Button>
            <Button onClick={() => navigate('/')} variant="primary" style={{ fontSize: 13 }}>
              Control Tower
            </Button>
          </div>
        </div>

        {/* TOP COMMAND HEADER */}
        <Card style={{ padding: 24, borderLeft: '6px solid #003DA5', backgroundColor: '#FFFFFF' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 16 }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 13, color: '#8A919B', fontWeight: 600 }}>
                  INCIDENT ID: {dossier.incident_id}
                </span>
                <span
                  style={{
                    fontSize: 12,
                    fontWeight: 700,
                    fontFamily: 'var(--font-mono)',
                    color: getStageTextColor(dossier.status),
                  }}
                >
                  ● {dossier.status?.replace(/_/g, ' ') || 'DETECTED'}
                </span>
                {isApproved && (
                  <span style={{ color: '#1E8E5A', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                    ● {approval?.approved_by ? `AUTHORIZED (${approval.approved_by.toUpperCase()})` : 'AUTHORIZED (OPERATIONS MANAGER)'}
                  </span>
                )}
                {isPendingApproval && (
                  <span style={{ color: '#B98900', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                    ● SIGN-OFF NEEDED
                  </span>
                )}
              </div>

              <h1 style={{ margin: '0 0 6px', fontSize: 24, fontWeight: 700, color: '#12161C' }}>
                {dossier.material_name || dossier.material_id}
                <code style={{ fontSize: 15, color: '#8A919B', marginLeft: 12, fontWeight: 500 }}>
                  [{dossier.material_id}]
                </code>
              </h1>

              <p style={{ margin: 0, fontSize: 14, color: '#3A4149', lineHeight: 1.5 }}>
                {dossier.description || `Disruption event detected on PO ${dossier.po_id || 'PO-7712'} with supplier ${dossier.supplier_name || dossier.supplier_id || 'SUP-21'}.`}
              </p>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 8 }}>
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <span style={{ fontSize: 13, color: '#8A919B' }}>Criticality:</span>
                <RiskBadge level={dossier.severity || 'HIGH'} />
              </div>
              <div style={{ fontSize: 12, color: '#8A919B', fontFamily: 'var(--font-mono)' }}>
                Detected: {new Date(dossier.created_at).toLocaleTimeString()} IST
              </div>
            </div>
          </div>
        </Card>

        {/* TAB CONTROLS */}
        <div style={{ display: 'flex', gap: 12, borderBottom: '2px solid #D5D8DC', paddingBottom: 8 }}>
          <button
            onClick={() => setActiveTab('demo_flow')}
            style={{
              background: 'none',
              border: 'none',
              padding: '8px 16px',
              fontSize: 15,
              fontWeight: 700,
              cursor: 'pointer',
              color: activeTab === 'demo_flow' ? '#003DA5' : '#8A919B',
              borderBottom: activeTab === 'demo_flow' ? '3px solid #003DA5' : '3px solid transparent',
              marginBottom: -10,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>▶</span> Minimum Demo Flow (9-Step Sequence)
          </button>

          <button
            onClick={() => setActiveTab('mvp_suite')}
            style={{
              background: 'none',
              border: 'none',
              padding: '8px 16px',
              fontSize: 15,
              fontWeight: 700,
              cursor: 'pointer',
              color: activeTab === 'mvp_suite' ? '#003DA5' : '#8A919B',
              borderBottom: activeTab === 'mvp_suite' ? '3px solid #003DA5' : '3px solid transparent',
              marginBottom: -10,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>★</span> Strong MVP Features (10 Capabilities Suite)
          </button>
        </div>

        {/* ========================================================================= */}
        {/* TAB 1: MINIMUM DEMO FLOW (9 STEPS IN SEQUENCE)                            */}
        {/* ========================================================================= */}
        {activeTab === 'demo_flow' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            
            {/* 1. DELAY INJECTED */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ backgroundColor: '#003DA5', color: '#FFFFFF', padding: '3px 8px', fontSize: 12, fontWeight: 700, borderRadius: 3 }}>
                    STEP 1
                  </span>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                    1. Supplier Delay Injected
                  </h3>
                </div>
                <span style={{ color: '#1E8E5A', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  ✓ EVENT INJECTED
                </span>
              </div>
              <p style={{ margin: '0 0 10px', fontSize: 14, color: '#3A4149' }}>
                {demoSteps[0]?.summary || `Disruption event injected on PO ${dossier.po_id || 'PO-7712'} with supplier ${dossier.supplier_name || 'SUP-21'}.`}
              </p>
              <div style={{ display: 'flex', gap: 16, backgroundColor: '#F4F5F7', padding: '10px 14px', borderRadius: 4, fontSize: 13 }}>
                <div><strong>Purchase Order:</strong> {dossier.po_id || 'PO-7712'}</div>
                <div><strong>Supplier:</strong> {dossier.supplier_name || 'Apex Auto Parts'} ({dossier.supplier_id || 'SUP-21'})</div>
                <div><strong>Reported Delay:</strong> +5 Days</div>
                <div><strong>Component:</strong> {dossier.material_name || dossier.material_id}</div>
              </div>
            </Card>

            {/* 2. DISRUPTION DETECTED */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ backgroundColor: '#003DA5', color: '#FFFFFF', padding: '3px 8px', fontSize: 12, fontWeight: 700, borderRadius: 3 }}>
                    STEP 2
                  </span>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                    2. Autonomous Disruption Detection
                  </h3>
                </div>
                <span style={{ color: '#1E8E5A', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  ✓ DETECTED BY ALERT ENGINE
                </span>
              </div>
              <p style={{ margin: '0 0 10px', fontSize: 14, color: '#3A4149' }}>
                {demoSteps[1]?.summary || `Autonomous Alert Engine triggered on breach of minimum safety stock threshold.`}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, backgroundColor: '#F4F5F7', padding: '10px 14px', borderRadius: 4, fontSize: 13 }}>
                <div><strong>Disruption Type:</strong> {dossier.incident_type?.replace(/_/g, ' ')}</div>
                <div><strong>Incident Rating:</strong> <RiskBadge level={dossier.severity || 'HIGH'} /></div>
                <div><strong>Detection Latency:</strong> &lt; 250ms</div>
              </div>
            </Card>

            {/* 3. INVENTORY & PRODUCTION IMPACT */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ backgroundColor: '#003DA5', color: '#FFFFFF', padding: '3px 8px', fontSize: 12, fontWeight: 700, borderRadius: 3 }}>
                    STEP 3
                  </span>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                    3. Inventory & Production Impact Analysis
                  </h3>
                </div>
                <span style={{ color: '#C4302B', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  ● CRITICAL BUFFER SHORTAGE
                </span>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 14, color: '#3A4149' }}>
                {doNothing.summary || `Stockout occurs in ${currentRisk.hours_to_stop || 48} hours without mitigation.`}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                <div style={{ padding: '12px 14px', backgroundColor: '#F4F5F7', border: '1px solid #D5D8DC', borderRadius: 4 }}>
                  <div style={{ fontSize: 12, color: '#8A919B' }}>USABLE INVENTORY</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#12161C' }}>{currentRisk.usable_stock?.toLocaleString()} units</div>
                </div>
                <div style={{ padding: '12px 14px', backgroundColor: '#F4F5F7', border: '1px solid #D5D8DC', borderRadius: 4 }}>
                  <div style={{ fontSize: 12, color: '#8A919B' }}>DAYS OF COVERAGE</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: currentRisk.coverage_days < 7 ? '#C4302B' : '#1E8E5A' }}>
                    {currentRisk.coverage_days} Days
                  </div>
                </div>
                <div style={{ padding: '12px 14px', backgroundColor: '#F4F5F7', border: '1px solid #D5D8DC', borderRadius: 4 }}>
                  <div style={{ fontSize: 12, color: '#8A919B' }}>HOURS TO PLANT HALT</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#C4302B' }}>{currentRisk.hours_to_stop} Hours</div>
                </div>
                <div style={{ padding: '12px 14px', backgroundColor: '#F4F5F7', border: '1px solid #D5D8DC', borderRadius: 4 }}>
                  <div style={{ fontSize: 12, color: '#8A919B' }}>7-DAY BURN RATE</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#12161C' }}>{currentRisk.consumption_7d} u/day</div>
                </div>
              </div>
            </Card>

            {/* 4. ORIGINAL SUPPLIER CONTACT */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ backgroundColor: '#003DA5', color: '#FFFFFF', padding: '3px 8px', fontSize: 12, fontWeight: 700, borderRadius: 3 }}>
                    STEP 4
                  </span>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                    4. Original Supplier Communication
                  </h3>
                </div>
                <Link to="/inbox" style={{ fontSize: 12, color: '#003DA5', fontWeight: 600, textDecoration: 'none' }}>
                  View in Inbox &rarr;
                </Link>
              </div>
              <p style={{ margin: '0 0 10px', fontSize: 14, color: '#3A4149' }}>
                Logged supplier delay notification and dispatched automated telemetry status confirmation request to {dossier.supplier_name || 'SUP-21'}.
              </p>
              <div style={{ backgroundColor: '#F4F5F7', padding: '10px 14px', borderRadius: 4, fontSize: 13, borderLeft: '4px solid #B98900' }}>
                <code>[INBOX INBOUND] SUP-21: Logistics disruption on PO-7712. Delivery delayed by 5 days. Revised ETA Sept 9.</code>
              </div>
            </Card>

            {/* 5. ALTERNATE SUPPLIER RFQS */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ backgroundColor: '#003DA5', color: '#FFFFFF', padding: '3px 8px', fontSize: 12, fontWeight: 700, borderRadius: 3 }}>
                    STEP 5
                  </span>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                    5. Alternate Supplier RFQ Broadcast
                  </h3>
                </div>
                <span style={{ color: '#1E8E5A', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  ✓ BROADCAST DISPATCHED
                </span>
              </div>
              <p style={{ margin: '0 0 10px', fontSize: 14, color: '#3A4149' }}>
                Disruption recovery agent broadcast emergency RFQs to {dossier.supplier_comparison?.length || 4} regional certified suppliers for emergency capacity allocation.
              </p>
              <div style={{ backgroundColor: '#F4F5F7', padding: '10px 14px', borderRadius: 4, fontSize: 13, borderLeft: '4px solid #003DA5' }}>
                <code>[OUTBOUND RFQ] Broadcast sent to SUP-34 (Metro Auto Parts) & SUP-41 (Rapid Auto Components) for emergency rate and 48h lead-time confirmation.</code>
              </div>
            </Card>

            {/* 6. MULTI-CRITERIA OPTIONS COMPARISON */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ backgroundColor: '#003DA5', color: '#FFFFFF', padding: '3px 8px', fontSize: 12, fontWeight: 700, borderRadius: 3 }}>
                    STEP 6
                  </span>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                    6. Multi-Criteria Options Comparison Matrix
                  </h3>
                </div>
                <span style={{ fontSize: 12, color: '#8A919B' }}>Deterministic Hard Filter Applied</span>
              </div>
              
              <Table>
                <thead>
                  <tr>
                    <Th>SUPPLIER CANDIDATE</Th>
                    <Th>PRICE / UNIT</Th>
                    <Th>LEAD TIME</Th>
                    <Th>AVAILABLE QTY</Th>
                    <Th>ISO / AQL COMPLIANCE</Th>
                    <Th>RELIABILITY</Th>
                    <Th>SCORE</Th>
                    <Th>SELECTION VERDICT</Th>
                  </tr>
                </thead>
                <tbody>
                  {dossier.supplier_comparison?.map((s) => (
                    <tr key={s.supplier_id} style={{ backgroundColor: s.is_selected ? 'rgba(0, 61, 165, 0.04)' : 'transparent' }}>
                      <Td>
                        <strong>{s.supplier_name}</strong>
                        <div style={{ fontSize: 11, color: '#8A919B' }}>{s.supplier_id}</div>
                      </Td>
                      <Td style={{ fontFamily: 'var(--font-mono)' }}>₹{s.unit_price?.toFixed(2)}</Td>
                      <Td style={{ fontFamily: 'var(--font-mono)' }}>{s.lead_time_days}d</Td>
                      <Td style={{ fontFamily: 'var(--font-mono)' }}>{s.available_quantity?.toLocaleString()}u</Td>
                      <Td>
                        {s.certification_valid ? (
                          <span style={{ color: '#1E8E5A', fontSize: 12, fontWeight: 600 }}>✓ ISO 9001 VALID</span>
                        ) : (
                          <span style={{ color: '#C4302B', fontSize: 12, fontWeight: 600 }}>✕ CERT EXPIRED</span>
                        )}
                      </Td>
                      <Td style={{ fontFamily: 'var(--font-mono)' }}>{s.reliability_score}%</Td>
                      <Td style={{ fontWeight: 700, fontFamily: 'var(--font-mono)' }}>{s.score}</Td>
                      <Td>
                        {s.is_selected ? (
                          <span style={{ color: '#1E8E5A', fontWeight: 700, fontSize: 12 }}>● SELECTED</span>
                        ) : s.rejection_reason ? (
                          <span style={{ color: '#C4302B', fontSize: 12 }}>✕ {s.rejection_reason}</span>
                        ) : (
                          <span style={{ color: '#8A919B', fontSize: 12 }}>ELIGIBLE</span>
                        )}
                      </Td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </Card>

            {/* 7. RECOMMENDED DECISION BLOCK & HUMAN APPROVAL ACTION GATE */}
            <Card style={{ padding: 24, border: '2px solid #003DA5', backgroundColor: '#FFFFFF' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ backgroundColor: '#003DA5', color: '#FFFFFF', padding: '3px 8px', fontSize: 12, fontWeight: 700, borderRadius: 3 }}>
                    STEP 7
                  </span>
                  <h3 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#12161C' }}>
                    7. Recommended Recovery Plan & Decision Gate
                  </h3>
                </div>
                <div>
                  {isApproved ? (
                    <span style={{ color: '#1E8E5A', fontSize: 13, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                      ● AUTHORIZED (OPERATIONS MANAGER)
                    </span>
                  ) : (
                    <span style={{ color: '#B98900', fontSize: 13, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                      ● AWAITING MANAGER SIGN-OFF
                    </span>
                  )}
                </div>
              </div>

              {plan ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                  <div>
                    <h4 style={{ margin: '0 0 6px', fontSize: 16, color: '#003DA5' }}>{plan.plan_name}</h4>
                    <p style={{ margin: 0, fontSize: 14, color: '#3A4149', lineHeight: 1.5 }}>
                      <strong>Operational Rationale:</strong> {plan.rationale}
                    </p>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                    <div style={{ backgroundColor: '#F4F5F7', padding: '12px 14px', borderRadius: 4 }}>
                      <div style={{ fontSize: 11, color: '#8A919B' }}>PRIMARY SUPPLIER</div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: '#12161C' }}>{plan.supplier_name}</div>
                    </div>
                    <div style={{ backgroundColor: '#F4F5F7', padding: '12px 14px', borderRadius: 4 }}>
                      <div style={{ fontSize: 11, color: '#8A919B' }}>TOTAL ORDER COST</div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: '#12161C', fontFamily: 'var(--font-mono)' }}>
                        ₹{plan.estimated_cost?.toLocaleString()}
                      </div>
                    </div>
                    <div style={{ backgroundColor: '#F4F5F7', padding: '12px 14px', borderRadius: 4 }}>
                      <div style={{ fontSize: 11, color: '#8A919B' }}>ESTIMATED DELIVERY</div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: '#12161C' }}>{plan.estimated_delivery_days} Days</div>
                    </div>
                    <div style={{ backgroundColor: '#F4F5F7', padding: '12px 14px', borderRadius: 4 }}>
                      <div style={{ fontSize: 11, color: '#8A919B' }}>ROBUSTNESS SCORE</div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: '#1E8E5A' }}>{plan.overall_score} / 100</div>
                    </div>
                  </div>

                  {/* Fact Validation Checks */}
                  <div style={{ backgroundColor: '#F4F5F7', padding: '12px 14px', borderRadius: 4 }}>
                    <div style={{ fontSize: 12, fontWeight: 700, color: '#12161C', marginBottom: 6 }}>
                      DETERMINISTIC VALIDATION FACTS:
                    </div>
                    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 13, color: '#1E8E5A' }}>
                      {plan.why_this_plan?.map((fact, idx) => (
                        <span key={idx}>{fact}</span>
                      ))}
                    </div>
                  </div>

                  {/* PROMINENT APPROVAL / REJECT / DISPATCH BUTTONS */}
                  <div
                    style={{
                      marginTop: 8,
                      padding: 16,
                      backgroundColor: '#1E242C',
                      borderRadius: 6,
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      flexWrap: 'wrap',
                      gap: 12,
                    }}
                  >
                    <div>
                      <div style={{ color: '#FFFFFF', fontWeight: 700, fontSize: 14 }}>
                        {isApproved ? 'Plan Authorized for ERP Execution' : 'Human-in-the-Loop Decision Gate'}
                      </div>
                      <div style={{ color: '#8A919B', fontSize: 12 }}>
                        {isApproved
                          ? 'Operational approval granted by Operations Manager. Purchase order ready for dispatch.'
                          : `Estimated cost (₹${plan.estimated_cost?.toLocaleString()}) requires manager authorization before commitment.`}
                      </div>
                    </div>

                    <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                      {isPendingApproval && (
                        <>
                          <Button
                            onClick={handleApprove}
                            disabled={actionLoading}
                            variant="primary"
                            style={{ fontSize: 13, padding: '9px 20px', fontWeight: 700 }}
                          >
                            {actionLoading ? <Spinner size="sm" /> : '✓ Authorize Plan'}
                          </Button>
                          <Button
                            onClick={() => setShowRejectModal(true)}
                            disabled={actionLoading}
                            variant="secondary"
                            style={{ fontSize: 13, padding: '9px 16px' }}
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
                          style={{ fontSize: 13, padding: '9px 22px', fontWeight: 700, backgroundColor: '#1E8E5A' }}
                        >
                          {actionLoading ? <Spinner size="sm" /> : 'Dispatch Purchase Order to ERP →'}
                        </Button>
                      )}

                      {isExecuted && (
                        <span style={{ color: '#1E8E5A', fontSize: 13, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                          ✓ COMMITTED & RESOLVED IN ERP
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ color: '#8A919B', fontSize: 14 }}>No recovery plan formulated.</div>
              )}
            </Card>

            {/* 8. SIMULATED ERP UPDATE */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ backgroundColor: '#003DA5', color: '#FFFFFF', padding: '3px 8px', fontSize: 12, fontWeight: 700, borderRadius: 3 }}>
                    STEP 8
                  </span>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                    8. Simulated ERP State Update
                  </h3>
                </div>
                <span style={{ color: isExecuted ? '#1E8E5A' : '#8A919B', fontSize: 12, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                  {isExecuted ? '✓ ERP SYNCHRONIZED' : '● STAGED FOR DISPATCH'}
                </span>
              </div>
              <p style={{ margin: '0 0 10px', fontSize: 14, color: '#3A4149' }}>
                {isExecuted
                  ? `Recovery purchase order confirmed and committed to PostgreSQL ERP schema with active logistics tracking.`
                  : `Purchase order payload constructed; will commit to PostgreSQL procurement tables upon dispatch.`}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, backgroundColor: '#F4F5F7', padding: '10px 14px', borderRadius: 4, fontSize: 13 }}>
                <div><strong>Target Supplier:</strong> {plan?.supplier_id || 'SUP-34'}</div>
                <div><strong>ERP PO Status:</strong> {isExecuted ? 'CONFIRMED' : 'STAGED'}</div>
                <div><strong>Projected Coverage Restored:</strong> {plan?.simulation?.coverage_after_recovery_days || 28.5} Days</div>
              </div>
            </Card>

            {/* 9. AUDIT TRAIL */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ backgroundColor: '#003DA5', color: '#FFFFFF', padding: '3px 8px', fontSize: 12, fontWeight: 700, borderRadius: 3 }}>
                    STEP 9
                  </span>
                  <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                    9. Complete Audit Trail & Decision Milestones
                  </h3>
                </div>
                <Link to="/audit-trail" style={{ fontSize: 12, color: '#003DA5', fontWeight: 600, textDecoration: 'none' }}>
                  Full Audit Ledger &rarr;
                </Link>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {dossier.decision_timeline?.map((ev, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 12px',
                      backgroundColor: '#F4F5F7',
                      borderRadius: 4,
                      fontSize: 13,
                    }}
                  >
                    <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, color: '#8A919B' }}>
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : '00:00:00'}
                      </span>
                      <strong>{ev.action}</strong>
                      <span style={{ color: '#3A4149' }}>{ev.outcome}</span>
                    </div>
                    <span style={{ color: '#1E8E5A', fontSize: 11, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                      ✓ {ev.status}
                    </span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: STRONG MVP FEATURES (10 CAPABILITIES SUITE)                        */}
        {/* ========================================================================= */}
        {activeTab === 'mvp_suite' && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 16 }}>
            
            {/* FEATURE 1: SUPPLIER RELIABILITY MEMORY */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>🧠</span>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                  1. Supplier Reliability Memory
                </h3>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#3A4149', lineHeight: 1.5 }}>
                {mvp['1_supplier_reliability_memory']?.summary}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, backgroundColor: '#F4F5F7', padding: '10px 12px', borderRadius: 4, fontSize: 12 }}>
                <div><strong>Quality Pass:</strong> {mvp['1_supplier_reliability_memory']?.historical_quality_score}%</div>
                <div><strong>On-Time Rate:</strong> {mvp['1_supplier_reliability_memory']?.on_time_delivery_rate}%</div>
                <div><strong>Claim Mismatches:</strong> {mvp['1_supplier_reliability_memory']?.claim_mismatch_flags}</div>
              </div>
            </Card>

            {/* FEATURE 2: MULTI-STEP REPLANNING */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>🔄</span>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                  2. Multi-Step Adaptive Replanning
                </h3>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#3A4149', lineHeight: 1.5 }}>
                {mvp['2_multi_step_replanning']?.summary}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, backgroundColor: '#F4F5F7', padding: '10px 12px', borderRadius: 4, fontSize: 12 }}>
                <div><strong>Loop Engine:</strong> {mvp['2_multi_step_replanning']?.engine_state}</div>
                <div><strong>Iterations:</strong> {mvp['2_multi_step_replanning']?.replanning_iterations}</div>
                <div><strong>Gate Status:</strong> {mvp['2_multi_step_replanning']?.verification_status}</div>
              </div>
            </Card>

            {/* FEATURE 3: PRODUCTION RESCHEDULING */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>🏭</span>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                  3. Production Rescheduling & Prioritization
                </h3>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#3A4149', lineHeight: 1.5 }}>
                {mvp['3_production_rescheduling']?.summary}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, backgroundColor: '#F4F5F7', padding: '10px 12px', borderRadius: 4, fontSize: 12 }}>
                <div><strong>Priority Order:</strong> {mvp['3_production_rescheduling']?.critical_order_id}</div>
                <div><strong>Tier:</strong> {mvp['3_production_rescheduling']?.priority_tier}</div>
                <div><strong>Hours Saved:</strong> {mvp['3_production_rescheduling']?.hours_saved_by_resequencing}h</div>
              </div>
            </Card>

            {/* FEATURE 4: PARTIAL SHIPMENT STRATEGY */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>📦</span>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                  4. Partial Shipment & Split-Sourcing Strategy
                </h3>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#3A4149', lineHeight: 1.5 }}>
                {mvp['4_partial_shipment_strategy']?.summary}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, backgroundColor: '#F4F5F7', padding: '10px 12px', borderRadius: 4, fontSize: 12 }}>
                <div><strong>Split Active:</strong> {mvp['4_partial_shipment_strategy']?.split_sourcing_active ? 'YES' : 'SINGLE_VENDOR'}</div>
                <div><strong>Allocations:</strong> {mvp['4_partial_shipment_strategy']?.allocations_count} Supplier(s)</div>
                <div><strong>Fulfillment:</strong> 100% Demand</div>
              </div>
            </Card>

            {/* FEATURE 5: BUDGET-AWARE OPTIMIZATION */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>💰</span>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                  5. Budget-Aware Optimization
                </h3>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#3A4149', lineHeight: 1.5 }}>
                {mvp['5_budget_aware_optimization']?.summary}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, backgroundColor: '#F4F5F7', padding: '10px 12px', borderRadius: 4, fontSize: 12 }}>
                <div><strong>Plan Cost:</strong> ₹{mvp['5_budget_aware_optimization']?.estimated_recovery_cost?.toLocaleString()}</div>
                <div><strong>Threshold:</strong> ₹{mvp['5_budget_aware_optimization']?.autonomous_spending_threshold?.toLocaleString()}</div>
                <div><strong>Variance:</strong> {mvp['5_budget_aware_optimization']?.cost_variance_vs_baseline}</div>
              </div>
            </Card>

            {/* FEATURE 6: ADVERSARIAL SUPPLIER HANDLING */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>🛡️</span>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                  6. Adversarial Supplier & Carrier Telemetry
                </h3>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#3A4149', lineHeight: 1.5 }}>
                {mvp['6_adversarial_supplier_handling']?.summary}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, backgroundColor: '#F4F5F7', padding: '10px 12px', borderRadius: 4, fontSize: 12 }}>
                <div><strong>Carrier API:</strong> {mvp['6_adversarial_supplier_handling']?.carrier_tracking_verification}</div>
                <div><strong>Tracking:</strong> {mvp['6_adversarial_supplier_handling']?.tracking_number}</div>
                <div><strong>Contradiction:</strong> {mvp['6_adversarial_supplier_handling']?.status_discrepancy_detected ? 'DETECTED' : 'NONE'}</div>
              </div>
            </Card>

            {/* FEATURE 7: HUMAN APPROVAL WORKFLOW */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>👤</span>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                  7. Human Approval Workflow
                </h3>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#3A4149', lineHeight: 1.5 }}>
                {mvp['7_human_approval_workflow']?.summary}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, backgroundColor: '#F4F5F7', padding: '10px 12px', borderRadius: 4, fontSize: 12 }}>
                <div><strong>Approval ID:</strong> {mvp['7_human_approval_workflow']?.approval_id}</div>
                <div><strong>Sign-off:</strong> {mvp['7_human_approval_workflow']?.authorized_by}</div>
                <div><strong>Status:</strong> {mvp['7_human_approval_workflow']?.status}</div>
              </div>
            </Card>

            {/* FEATURE 8: VISUAL DASHBOARD TELEMETRY */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>📊</span>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                  8. Visual Operational Telemetry
                </h3>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#3A4149', lineHeight: 1.5 }}>
                {mvp['8_visual_dashboard_telemetry']?.summary}
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, backgroundColor: '#F4F5F7', padding: '10px 12px', borderRadius: 4, fontSize: 12 }}>
                <div><strong>Coverage:</strong> {mvp['8_visual_dashboard_telemetry']?.days_of_coverage} Days</div>
                <div><strong>Halt Time:</strong> {mvp['8_visual_dashboard_telemetry']?.hours_to_line_stop}h</div>
                <div><strong>Risk Level:</strong> {mvp['8_visual_dashboard_telemetry']?.risk_severity}</div>
              </div>
            </Card>

            {/* FEATURE 9: SIMULATION REPLAY */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>⏪</span>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                  9. Simulation Replay & What-If Branching
                </h3>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#3A4149', lineHeight: 1.5 }}>
                {mvp['9_simulation_replay']?.summary}
              </p>
              <div style={{ backgroundColor: '#F4F5F7', padding: '10px 12px', borderRadius: 4, fontSize: 12 }}>
                <div style={{ marginBottom: 4 }}><strong>Branch A (Do Nothing):</strong> {mvp['9_simulation_replay']?.branch_a_do_nothing}</div>
                <div><strong>Branch B (Optimal Mitigation):</strong> {mvp['9_simulation_replay']?.branch_b_recommended}</div>
              </div>
            </Card>

            {/* FEATURE 10: TOOL-CALL TRACE VIEWER */}
            <Card style={{ padding: 20 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 18 }}>🛠️</span>
                <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#12161C' }}>
                  10. Agent Tool-Call Trace Viewer
                </h3>
              </div>
              <p style={{ margin: '0 0 12px', fontSize: 13, color: '#3A4149', lineHeight: 1.5 }}>
                {mvp['10_tool_call_trace_viewer']?.summary}
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 180, overflowY: 'auto' }}>
                {mvp['10_tool_call_trace_viewer']?.traces?.map((tr, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', backgroundColor: '#F4F5F7', padding: '6px 10px', borderRadius: 3, fontSize: 11, fontFamily: 'var(--font-mono)' }}>
                    <span>Step {tr.step}: {tr.tool}()</span>
                    <span style={{ color: tr.status === 'SUCCESS' ? '#1E8E5A' : '#003DA5' }}>{tr.latency_ms}ms ({tr.status})</span>
                  </div>
                ))}
              </div>
            </Card>

          </div>
        )}

      </div>

      {/* REJECT MODAL */}
      {showRejectModal && (
        <Modal title="Reject Recovery Plan" onClose={() => setShowRejectModal(false)}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <p style={{ fontSize: 14, color: '#3A4149', margin: 0 }}>
              Specify the operational or budget justification for rejecting this recovery recommendation:
            </p>
            <Input
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              placeholder="e.g. Total cost exceeds budget ceiling; seek alternative regional supplier."
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              <Button onClick={() => setShowRejectModal(false)} variant="secondary">Cancel</Button>
              <Button onClick={handleReject} disabled={actionLoading} variant="primary" style={{ backgroundColor: '#C4302B' }}>
                Confirm Rejection
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </Layout>
  );
}
