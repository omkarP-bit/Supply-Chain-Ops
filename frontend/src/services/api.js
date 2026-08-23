const BASE = '/api/v1';

async function request(method, path, body) {
  const opts = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(`${BASE}${path}`, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const message = err.message || (typeof err.detail === 'string' ? err.detail : err.detail?.message) || `HTTP ${res.status}`;
    throw new Error(message);
  }
  return res.json();
}

const api = {
  health: () => fetch('/health').then(r => r.json()),

  // Dashboard & Incidents Control Tower
  getDashboard: () => request('GET', '/dashboard'),
  listIncidents: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request('GET', `/incidents${q ? '?' + q : ''}`);
  },
  getIncident: (id) => request('GET', `/incidents/${id}`),
  getIncidentDossier: (id) => request('GET', `/incidents/${id}/dossier`).catch(() => request('GET', `/incidents/${id}`)),
  createIncident: (data) => request('POST', '/incidents', data),
  analyzeIncident: (id) => request('POST', `/incidents/${id}/analyze`),
  recommendPlans: (id) => request('POST', `/incidents/${id}/recommend`),
  getPlans: (id) => request('GET', `/incidents/${id}/plans`),

  // Inventory & Coverage APIs
  getInventory: () => request('GET', '/inventory'),
  getInventoryItem: (id) => request('GET', `/inventory/${id}`),
  getCoverage: (id) => request('GET', `/inventory/${id}/coverage`).catch(() => request('GET', `/inventory/${id}`)),
  getInventoryHistory: (id, days = 35) => request('GET', `/inventory/${id}/history?days=${days}`),

  // Suppliers APIs
  listSuppliers: () => request('GET', '/contract-suppliers').catch(() => request('GET', '/suppliers')),
  getSuppliers: () => request('GET', '/contract-suppliers'),
  getSupplier: (id) => request('GET', `/suppliers/${id}`),
  getEligibleSuppliers: (materialId, qty = 100, deadlineDays = null) => {
    const q = new URLSearchParams({ required_quantity: qty });
    if (deadlineDays) q.append('deadline_days', deadlineDays);
    return request('GET', `/suppliers/eligible/${materialId}?${q.toString()}`).catch(() => []);
  },

  // Purchase Orders & Schedule APIs
  getPurchaseOrders: () => request('GET', '/purchase-orders'),
  getPurchaseOrder: (id) => request('GET', `/purchase-orders/${id}`),
  patchPurchaseOrder: (id, data) => request('PATCH', `/purchase-orders/${id}`, data),
  getProductionSchedule: () => request('GET', '/production-schedule'),
  getSupplierMessages: () => request('GET', '/supplier-messages'),

  // Alert Engine APIs
  scanAlerts: () => request('POST', '/alerts/scan'),
  listAlerts: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request('GET', `/alerts${q ? '?' + q : ''}`);
  },
  getAlert: (id) => request('GET', `/alerts/${id}`),

  // Escalations & Approvals APIs
  listEscalations: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request('GET', `/escalations${q ? '?' + q : ''}`);
  },
  resolveEscalation: (id, decision, note = '') =>
    request('POST', `/escalations/${id}/resolve`, { decision, note }),
  listApprovals: () => request('GET', '/approvals'),
  getApproval: (id) => request('GET', `/approvals/${id}`),
  approveRequest: (id) => request('POST', `/approvals/${id}/approve`),
  rejectRequest: (id, reason) => request('POST', `/approvals/${id}/reject`, { reason }),
  executePlan: (planId, approvalId) =>
    request('POST', `/plans/${planId}/execute`, { plan_id: planId, approval_id: approvalId }),

  // Unified Audit Trail APIs
  getAuditLog: async (params = {}) => {
    const q = new URLSearchParams(params).toString();
    try {
      const [contractLogs, workflowEvents] = await Promise.all([
        request('GET', `/audit-log${q ? '?' + q : ''}`).catch(() => []),
        request('GET', `/audit${q ? '?' + q : ''}`).catch(() => []),
      ]);
      const unified = [
        ...contractLogs.map((l) => ({
          audit_id: l.audit_id || `CLOG-${l.id}`,
          ts: l.ts,
          event_type: l.event_type,
          entity_type: l.entity_type || 'SYSTEM',
          entity_id: l.entity_id || '-',
          actor: l.actor || 'System Engine',
          details: l.after || l.before || {},
          before: l.before,
          after: l.after,
        })),
        ...workflowEvents.map((e) => ({
          audit_id: e.event_id || `WEV-${e.id}`,
          ts: e.timestamp,
          event_type: e.event_type,
          entity_type: 'INCIDENT',
          entity_id: e.incident_id || '-',
          actor: e.agent_name || 'Autonomous Agent',
          details: e.output_data || { action: e.action, reason: e.reason },
          before: e.input_data,
          after: e.output_data,
          action: e.action,
          reason: e.reason,
        })),
      ];
      unified.sort((a, b) => new Date(b.ts || 0) - new Date(a.ts || 0));
      return unified;
    } catch {
      return [];
    }
  },
  // Scenario Lab Simulation & Injection APIs
  listScenarios: () => request('GET', '/scenarios'),
  injectScenario: (scenarioId) => request('POST', `/scenarios/${scenarioId}/inject`),
  resetScenario: (scenarioId) => request('POST', `/scenarios/${scenarioId}/reset`),
};

export default api;
