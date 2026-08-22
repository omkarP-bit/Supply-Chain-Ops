import React from 'react';

const STEPS = [
  { id: 'detect', label: '1. Disruption Detection', sub: 'Alert Engine (5 Rules)' },
  { id: 'supervisor', label: '2. Supervisor Analysis', sub: 'Risk & 7d/30d Trend' },
  { id: 'supplier', label: '3. Hard Filtering', sub: 'AQL, Certs & MOQ' },
  { id: 'recovery', label: '4. Recovery Agent', sub: 'LLM Multi-Sourcing' },
  { id: 'simulation', label: '5. What-If Sim', sub: 'Validation & Stress Test' },
  { id: 'approval', label: '6. Human Approval', sub: 'Manager Sign-off' },
  { id: 'verify', label: '7. Verification', sub: 'Continuous Loop' },
];

export default function WorkflowStepper({ currentStep = 'detect', onStepClick }) {
  const getStepIndex = (id) => {
    const map = {
      detect: 0,
      scan: 0,
      analyze: 1,
      analyzing: 1,
      supervisor: 1,
      supplier: 2,
      recovery: 3,
      recommending: 3,
      proposed: 3,
      simulation: 4,
      validated: 4,
      approval: 5,
      pending_approval: 5,
      approved: 5,
      executing: 5,
      verify: 6,
      completed: 6,
      resolved: 6,
    };
    return map[currentStep?.toLowerCase()] ?? 0;
  };

  const activeIdx = getStepIndex(currentStep);

  return (
    <div
      style={{
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: 12,
        padding: '16px 20px',
        marginBottom: 24,
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 13, fontWeight: 700, color: '#0f172a', textTransform: 'uppercase', letterSpacing: 0.5 }}>
            ⚡ Autonomous Agent Workflow Stage
          </span>
          <span
            style={{
              fontSize: 11,
              padding: '2px 8px',
              borderRadius: 12,
              background: '#e0f2fe',
              color: '#0369a1',
              fontWeight: 600,
            }}
          >
            Phase: {STEPS[activeIdx]?.label || 'Active'}
          </span>
        </div>
        <span style={{ fontSize: 12, color: '#64748b' }}>
          Loop: <strong>Observe → Decide → Act → Verify → Replan</strong>
        </span>
      </div>

      <div style={{ display: 'flex', gap: 8, overflowX: 'auto', paddingBottom: 4 }}>
        {STEPS.map((step, idx) => {
          const isCurrent = idx === activeIdx;
          const isPassed = idx < activeIdx;

          return (
            <div
              key={step.id}
              onClick={() => onStepClick?.(step.id)}
              style={{
                flex: 1,
                minWidth: 130,
                padding: '10px 12px',
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
                  fontSize: 10,
                  marginTop: 2,
                  color: isCurrent ? '#94a3b8' : isPassed ? '#15803d' : '#94a3b8',
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
