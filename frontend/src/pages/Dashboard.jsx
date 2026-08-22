import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid, Legend,
  PieChart, Pie, Cell
} from 'recharts';
import api from '../services/api';
import Layout from '../components/Layout';
import WorkflowStepper from '../components/WorkflowStepper';
import ScenarioRunner from '../components/ScenarioRunner';
import { Card, Button, Spinner, Table, Th, Td } from '../components/UI';

const ALERT_TYPE_LABELS = {
  po_delayed: 'PO Delayed',
  inventory_below_safety_stock: 'Low Safety Stock',
  supplier_response_pending: 'Supplier Pending',
  budget_approval_required: 'Budget Approval',
  production_schedule_at_risk: 'Prod Schedule Risk',
};

const SEVERITY_COLORS = {
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#3b82f6',
};

const PIE_COLORS = {
  approved: '#10b981',
  pending: '#f59e0b',
  rejected: '#ef4444',
};

export default function Dashboard() {
  const [alerts, setAlerts] = useState([]);
  const [escalations, setEscalations] = useState([]);
  const [inventory, setInventory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [selectedType, setSelectedType] = useState('ALL');
  const [currentStage, setCurrentStage] = useState('detect');
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [alertsData, escData, invData] = await Promise.all([
        api.listAlerts(),
        api.listEscalations(),
        api.getInventory(),
      ]);
      setAlerts(alertsData || []);
      setEscalations(escData || []);
      setInventory(invData || []);

      const pendingEsc = (escData || []).filter((e) => e.status === 'pending');
      if (pendingEsc.length > 0) {
        setCurrentStage('approval');
      } else if ((alertsData || []).some((a) => a.status === 'open')) {
        setCurrentStage('supervisor');
      } else {
        setCurrentStage('verify');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleScan = async () => {
    try {
      setScanning(true);
      setCurrentStage('detect');
      await api.scanAlerts();
      await loadData();
    } catch (err) {
      alert(`Scan failed: ${err.message}`);
    } finally {
      setScanning(false);
    }
  };

  // 1. Bar Chart Data (Alerts by Type)
  const barChartData = Object.keys(ALERT_TYPE_LABELS).map((type) => ({
    name: ALERT_TYPE_LABELS[type],
    count: alerts.filter((a) => a.type === type && a.status === 'open').length,
  }));

  // 2. Line Chart Data (Stock vs Safety Stock for low/at-risk components)
  const lineChartData = inventory
    .filter((item) => item.usable_stock <= item.safety_stock * 1.5)
    .map((item) => ({
      name: item.component_id,
      usableStock: item.usable_stock,
      safetyStock: item.safety_stock,
    }));

  // 3. Donut Chart Data (Escalation Outcomes)
  const pieChartData = [
    { name: 'Approved', value: escalations.filter((e) => e.status === 'approved').length, color: PIE_COLORS.approved },
    { name: 'Pending', value: escalations.filter((e) => e.status === 'pending').length, color: PIE_COLORS.pending },
    { name: 'Rejected', value: escalations.filter((e) => e.status === 'rejected').length, color: PIE_COLORS.rejected },
  ].filter((d) => d.value > 0);

  const openAlerts = alerts.filter((a) => a.status === 'open');
  const filteredAlerts = selectedType === 'ALL'
    ? openAlerts
    : openAlerts.filter((a) => a.type === selectedType);

  const pendingEscalationsCount = escalations.filter((e) => e.status === 'pending').length;

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#1e293b' }}>
            Autonomous Supply Chain Control Center
          </h1>
          <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>
            Continuous disruption detection, automated alert evaluation & multi-agent recovery loop
          </p>
        </div>
        <Button onClick={handleScan} disabled={scanning} style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {scanning ? <Spinner size="sm" /> : '⚡'}
          {scanning ? 'Scanning System...' : 'Run Alert Scan'}
        </Button>
      </div>

      {/* Multi-Agent Architecture Workflow Stepper */}
      <WorkflowStepper currentStep={currentStage} onStepClick={(s) => setCurrentStage(s)} />

      {/* Interactive Scenario Testing Studio */}
      <ScenarioRunner onScenarioComplete={loadData} />

      {error && (
        <div style={{ padding: 14, background: '#fee2e2', color: '#991b1b', borderRadius: 8, marginBottom: 20 }}>
          {error}
        </div>
      )}

      {/* KPI Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16, marginBottom: 24 }}>
        <Card style={{ padding: 20, borderLeft: '4px solid #ef4444' }}>
          <div style={{ fontSize: 13, color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Active Open Alerts</div>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#0f172a', marginTop: 4 }}>{openAlerts.length}</div>
          <div style={{ fontSize: 12, color: '#ef4444', marginTop: 4 }}>Requires immediate attention</div>
        </Card>
        <Card style={{ padding: 20, borderLeft: '4px solid #f59e0b' }}>
          <div style={{ fontSize: 13, color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Pending Escalations</div>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#0f172a', marginTop: 4 }}>{pendingEscalationsCount}</div>
          <div style={{ fontSize: 12, color: '#f59e0b', marginTop: 4 }}>
            <Link to="/escalations" style={{ color: '#d97706', textDecoration: 'none', fontWeight: 600 }}>Review in Queue →</Link>
          </div>
        </Card>
        <Card style={{ padding: 20, borderLeft: '4px solid #3b82f6' }}>
          <div style={{ fontSize: 13, color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>Components Monitored</div>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#0f172a', marginTop: 4 }}>{inventory.length}</div>
          <div style={{ fontSize: 12, color: '#3b82f6', marginTop: 4 }}>
            <Link to="/inventory" style={{ color: '#2563eb', textDecoration: 'none', fontWeight: 600 }}>View Inventory →</Link>
          </div>
        </Card>
        <Card style={{ padding: 20, borderLeft: '4px solid #10b981' }}>
          <div style={{ fontSize: 13, color: '#64748b', fontWeight: 600, textTransform: 'uppercase' }}>System Health</div>
          <div style={{ fontSize: 32, fontWeight: 700, color: '#10b981', marginTop: 4 }}>OPERATIONAL</div>
          <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>PostgreSQL & Multi-Agent Active</div>
        </Card>
      </div>

      {/* Visual Analytics Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 20, marginBottom: 24 }}>
        {/* 1. Bar Chart: Alerts by Type */}
        <Card style={{ padding: 20 }}>
          <h3 style={{ margin: '0 0 16px', fontSize: 15, fontWeight: 600, color: '#1e293b' }}>
            Alerts Distribution by Rule Category
          </h3>
          <div style={{ width: '100%', height: 240 }}>
            <ResponsiveContainer>
              <BarChart data={barChartData} margin={{ top: 10, right: 10, left: -20, bottom: 20 }}>
                <XAxis dataKey="name" angle={-15} textAnchor="end" tick={{ fontSize: 11, fill: '#64748b' }} interval={0} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip />
                <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* 2. Line Chart: Usable vs Safety Stock */}
        <Card style={{ padding: 20 }}>
          <h3 style={{ margin: '0 0 16px', fontSize: 15, fontWeight: 600, color: '#1e293b' }}>
            Usable Stock vs Safety Stock Thresholds
          </h3>
          <div style={{ width: '100%', height: 240 }}>
            <ResponsiveContainer>
              <LineChart data={lineChartData} margin={{ top: 10, right: 10, left: -10, bottom: 20 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="usableStock" name="Usable Stock" stroke="#3b82f6" strokeWidth={2} dot={{ r: 4 }} />
                <Line type="monotone" dataKey="safetyStock" name="Safety Stock" stroke="#ef4444" strokeWidth={2} strokeDasharray="4 4" dot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        {/* 3. Donut Chart: Escalation Outcomes */}
        <Card style={{ padding: 20 }}>
          <h3 style={{ margin: '0 0 16px', fontSize: 15, fontWeight: 600, color: '#1e293b' }}>
            Human Escalation Resolution Ratios
          </h3>
          <div style={{ width: '100%', height: 240, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {pieChartData.length === 0 ? (
              <div style={{ color: '#94a3b8', fontSize: 13 }}>No escalation data yet</div>
            ) : (
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={pieChartData}
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieChartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
        </Card>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16, flexWrap: 'wrap' }}>
        <button
          onClick={() => setSelectedType('ALL')}
          style={{
            padding: '6px 12px',
            borderRadius: 6,
            border: '1px solid #cbd5e1',
            background: selectedType === 'ALL' ? '#0f172a' : '#fff',
            color: selectedType === 'ALL' ? '#fff' : '#475569',
            fontSize: 12,
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          All Alerts ({openAlerts.length})
        </button>
        {Object.entries(ALERT_TYPE_LABELS).map(([type, label]) => {
          const count = openAlerts.filter((a) => a.type === type).length;
          return (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              style={{
                padding: '6px 12px',
                borderRadius: 6,
                border: '1px solid #cbd5e1',
                background: selectedType === type ? '#0f172a' : '#fff',
                color: selectedType === type ? '#fff' : '#475569',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {label} ({count})
            </button>
          );
        })}
      </div>

      {/* Open Alerts Table */}
      <Card style={{ padding: 20 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 40 }}><Spinner size="lg" /></div>
        ) : filteredAlerts.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 30, color: '#64748b' }}>
            No open alerts matching this filter.
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Alert ID</Th>
                <Th>Rule Category</Th>
                <Th>Entity</Th>
                <Th>Severity</Th>
                <Th>Message</Th>
                <Th>Requires Approval</Th>
                <Th>Detected At</Th>
              </tr>
            </thead>
            <tbody>
              {filteredAlerts.map((alert) => (
                <tr key={alert.alert_id}>
                  <Td><code style={{ fontWeight: 600 }}>{alert.alert_id.slice(0, 8)}</code></Td>
                  <Td>
                    <span style={{ fontSize: 12, fontWeight: 600, color: '#334155' }}>
                      {ALERT_TYPE_LABELS[alert.type] || alert.type}
                    </span>
                  </Td>
                  <Td>
                    <code style={{ background: '#f1f5f9', padding: '2px 6px', borderRadius: 4 }}>
                      {alert.entity_type}:{alert.entity_id}
                    </code>
                  </Td>
                  <Td>
                    <span
                      style={{
                        padding: '3px 8px',
                        borderRadius: 4,
                        fontSize: 11,
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        background:
                          alert.severity === 'high'
                            ? '#fee2e2'
                            : alert.severity === 'medium'
                            ? '#fef3c7'
                            : '#dbeafe',
                        color:
                          alert.severity === 'high'
                            ? '#991b1b'
                            : alert.severity === 'medium'
                            ? '#b45309'
                            : '#1e40af',
                      }}
                    >
                      {alert.severity}
                    </span>
                  </Td>
                  <Td style={{ maxWidth: 300, fontSize: 13 }}>{alert.message}</Td>
                  <Td>
                    {alert.requires_approval ? (
                      <span style={{ color: '#dc2626', fontWeight: 600, fontSize: 12 }}>
                        ⚠️ Yes (Auto-Escalated)
                      </span>
                    ) : (
                      <span style={{ color: '#16a34a', fontSize: 12 }}>Autonomous</span>
                    )}
                  </Td>
                  <Td style={{ fontSize: 12, color: '#64748b' }}>
                    {new Date(alert.created_at).toLocaleTimeString()}
                  </Td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </Layout>
  );
}
