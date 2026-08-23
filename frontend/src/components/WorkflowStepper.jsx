import React from 'react';

const STEPS = [
  { id: 'detect', label: '1. Detect', sub: 'Disruption Identified' },
  { id: 'assess', label: '2. Assess', sub: 'Operational Risk' },
  { id: 'evaluate', label: '3. Evaluate', sub: 'Supplier Eligibility' },
  { id: 'plan', label: '4. Plan', sub: 'Multi-Sourcing Strategy' },
  { id: 'validate', label: '5. Validate', sub: 'Stress Testing' },
  { id: 'approve', label: '6. Approve', sub: 'Human Authorization' },
  { id: 'execute', label: '7. Execute', sub: 'ERP PO Dispatch' },
  { id: 'verify', label: '8. Verify', sub: 'Post-Execution Audit' },
  { id: 'resolve', label: '9. Resolve', sub: 'Continuity Restored' },
];

export default function WorkflowStepper({ currentStep = 'detect', onStepClick }) {
  const getStepIndex = (raw) => {
    const s = String(raw || '').toLowerCase();
    if (s.includes('detect') || s.includes('scan') || s === 'open') return 0;
    if (s.includes('assess') || s.includes('analyz') || s.includes('supervisor')) return 1;
    if (s.includes('evaluat') || s.includes('supplier')) return 2;
    if (s.includes('plan') || s.includes('recommend')) return 3;
    if (s.includes('validat') || s.includes('simulat')) return 4;
    if (s.includes('approv') || s.includes('pending')) return 5;
    if (s.includes('execut')) return 6;
    if (s.includes('verify') || s.includes('verif')) return 7;
    if (s.includes('replan')) return 3;
    if (s.includes('resolv') || s.includes('complet')) return 8;
    return 5;
  };

  const activeIdx = getStepIndex(currentStep);

  const getStatusLabel = () => {
    const s = String(currentStep || '').toUpperCase();
    if (s.includes('APPROV') || s.includes('PENDING')) return 'WAITING FOR HUMAN APPROVAL';
    if (s.includes('EXECUT')) return 'EXECUTING';
    if (s.includes('VERIF')) return 'VERIFYING OUTCOME';
    if (s.includes('REPLAN')) return 'REPLANNING';
    if (s.includes('RESOLV') || s.includes('COMPLET')) return 'RESOLVED';
    return STEPS[activeIdx]?.label.toUpperCase() || 'IN PROGRESS';
  };

  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: 12,
        padding: '16px 20px',
        marginBottom: 20,
        boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: '#0f172a', textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Operational Workflow Engine
          </span>
          <span
            style={{
              fontSize: 11,
              padding: '3px 10px',
              borderRadius: 12,
              background: currentStep?.toLowerCase().includes('approv') ? '#fef3c7' : '#e0f2fe',
              color: currentStep?.toLowerCase().includes('approv') ? '#92400e' : '#0369a1',
              fontWeight: 700,
            }}
          >
            ● {getStatusLabel()}
          </span>
        </div>
        <span style={{ fontSize: 11, color: '#64748b' }}>
          LangGraph Agentic Loop: <strong>Detect → Assess → Plan → Validate → Approve → Execute → Verify → Resolve</strong>
        </span>
      </div>

      <div style={{ display: 'flex', gap: 6, overflowX: 'auto', paddingBottom: 4 }}>
        {STEPS.map((step, idx) => {
          const isCurrent = idx === activeIdx;
          const isPassed = idx < activeIdx;

          return (
            <div
              key={step.id}
              onClick={() => onStepClick?.(step.id)}
              style={{
                flex: 1,
                minWidth: 105,
                padding: '8px 10px',
                borderRadius: 8,
                background: isCurrent
                  ? '#0f172a'
                  : isPassed
                  ? '#f0fdf4'
                  : '#f8fafc',
                border: `1px solid ${
                  isCurrent ? '#0f172a' : isPassed ? '#bbf7d0' : '#e2e8f0'
                }`,
                color: isCurrent ? '#ffffff' : isPassed ? '#166534' : '#64748b',
                cursor: onStepClick ? 'pointer' : 'default',
                transition: 'all 0.2s ease',
              }}
            >
              <div style={{ fontSize: 11, fontWeight: 700, whiteSpace: 'nowrap' }}>
                {isPassed ? '✓ ' : ''}
                {step.label}
              </div>
              <div
                style={{
                  fontSize: 9,
                  marginTop: 2,
                  color: isCurrent ? '#94a3b8' : isPassed ? '#15803d' : '#94a3b8',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {step.sub}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
