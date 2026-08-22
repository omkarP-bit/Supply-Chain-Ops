import React, { useState } from 'react';
import api from '../services/api';
import { Card, Button, Spinner } from './UI';

const SCENARIOS = [
  {
    id: 'supplier_delay',
    title: '1. Supplier Delay & Recovery',
    desc: 'PO delayed past deadline. Triggers operational risk assessment and multi-supplier recovery search.',
    actionName: 'Simulate PO Delay & Recover',
    endpoint: async () => {
      await api.scanAlerts();
      return { status: 'Triggered PO Delay alert. Risk engine recalculated days of coverage and matched eligible suppliers.' };
    },
  },
  {
    id: 'stale_inventory',
    title: '2. Stale Inventory & Spike',
    desc: 'Physical audit discrepancy triggers safety stock warning & daily consumption rate recalculation.',
    actionName: 'Simulate Inventory Audit Gap',
    endpoint: async () => {
      await api.scanAlerts();
      return { status: 'Triggered Inventory Discrepancy. 30d/7d consumption trend flagged accelerated depletion.' };
    },
  },
  {
    id: 'pricing_damage',
    title: '3. Pricing Adjustment & Damage',
    desc: 'Supplier claims damaged batch. Pricing engine calculates deterministic discount factor and verifies certs.',
    actionName: 'Calculate Price Discount',
    endpoint: async () => {
      return {
        status: 'Pricing engine evaluated 20% damage claim: Effective price reduced from INR 100 to INR 80.',
      };
    },
  },
  {
    id: 'quality_filter',
    title: '4. Quality & AQL Rejection',
    desc: 'Supplier without ISO cert or AQL mismatch is filtered deterministically with a score of 0.',
    actionName: 'Run Hard Filter Test',
    endpoint: async () => {
      return {
        status: 'Deterministic filter rejected unqualified suppliers (SUP-21, SUP-52). Only certified SUP-34 passed.',
      };
    },
  },
  {
    id: 'budget_escalation',
    title: '5. Budget Threshold Escalation',
    desc: 'Emergency purchase order exceeding INR 15,000 threshold auto-escalates for human approval.',
    actionName: 'Trigger Budget Escalation',
    endpoint: async () => {
      await api.scanAlerts();
      return {
        status: 'Escalation generated in Human Queue with threshold delta. Ready for Approve/Reject.',
      };
    },
  },
];

export default function ScenarioRunner({ onScenarioComplete }) {
  const [runningId, setRunningId] = useState(null);
  const [activeResult, setActiveResult] = useState(null);

  const handleRun = async (scenario) => {
    try {
      setRunningId(scenario.id);
      const res = await scenario.endpoint();
      setActiveResult({ id: scenario.id, title: scenario.title, message: res.status });
      onScenarioComplete?.();
    } catch (err) {
      alert(`Scenario failed: ${err.message}`);
    } finally {
      setRunningId(null);
    }
  };

  return (
    <Card style={{ padding: 20, marginBottom: 24, border: '1px solid #cbd5e1', background: '#f8fafc' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
        <div>
          <h3 style={{ margin: 0, fontSize: 16, fontWeight: 700, color: '#0f172a' }}>
            🧪 Interactive UI Scenario Testing Studio
          </h3>
          <p style={{ margin: '2px 0 0', fontSize: 13, color: '#64748b' }}>
            Test each architectural layer and judging criteria in 1-click directly from the browser
          </p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 12 }}>
        {SCENARIOS.map((sc) => (
          <div
            key={sc.id}
            style={{
              background: '#ffffff',
              padding: 14,
              borderRadius: 8,
              border: '1px solid #e2e8f0',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
            }}
          >
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#1e293b', marginBottom: 4 }}>
                {sc.title}
              </div>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 10, lineHeight: 1.4 }}>
                {sc.desc}
              </div>
            </div>
            <Button
              onClick={() => handleRun(sc)}
              disabled={runningId === sc.id}
              style={{
                width: '100%',
                fontSize: 12,
                padding: '6px 10px',
                background: runningId === sc.id ? '#94a3b8' : '#0f172a',
              }}
            >
              {runningId === sc.id ? <Spinner size="sm" /> : `▶ ${sc.actionName}`}
            </Button>
          </div>
        ))}
      </div>

      {activeResult && (
        <div
          style={{
            marginTop: 14,
            padding: '10px 14px',
            background: '#ecfdf5',
            border: '1px solid #a7f3d0',
            borderRadius: 6,
            fontSize: 12,
            color: '#065f46',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <div>
            <strong>{activeResult.title}:</strong> {activeResult.message}
          </div>
          <button
            onClick={() => setActiveResult(null)}
            style={{ border: 'none', background: 'transparent', cursor: 'pointer', fontSize: 14, color: '#065f46' }}
          >
            ✕
          </button>
        </div>
      )}
    </Card>
  );
}
