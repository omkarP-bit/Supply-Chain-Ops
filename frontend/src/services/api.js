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

  // Dashboard & Legacy Incident Control Tower
  getDashboard: () => request('GET', '/dashboard'),
  listIncidents: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request('GET', `/incidents${q ? '?' + q : ''}`);
  },
  getIncident: (id) => request('GET', `/incidents/${id}`),
  createIncident: (data) => request('POST', '/incidents', data),
  analyzeIncident: (id) => request('POST', `/incidents/${id}/analyze`),
  recommendPlans: (id) => request('POST', `/incidents/${id}/recommend`),
  getPlans: (id) => request('GET', `/incidents/${id}/plans`),

  // Contract Core Data APIs
  getInventory: () => request('GET', '/inventory'),
  getInventoryItem: (id) => request('GET', `/inventory/${id}`),
  getPurchaseOrders: () => request('GET', '/purchase-orders'),
  getPurchaseOrder: (id) => request('GET', `/purchase-orders/${id}`),
  patchPurchaseOrder: (id, data) => request('PATCH', `/purchase-orders/${id}`, data),
  getSuppliers: () => request('GET', '/contract-suppliers'),
  getProductionSchedule: () => request('GET', '/production-schedule'),
  getSupplierMessages: () => request('GET', '/supplier-messages'),

  // Contract Alert Engine APIs
  scanAlerts: () => request('POST', '/alerts/scan'),
  listAlerts: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request('GET', `/alerts${q ? '?' + q : ''}`);
  },
  getAlert: (id) => request('GET', `/alerts/${id}`),

  // Contract Escalations & Approval APIs
  listEscalations: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request('GET', `/escalations${q ? '?' + q : ''}`);
  },
  resolveEscalation: (id, decision, note = '') =>
    request('POST', `/escalations/${id}/resolve`, { decision, note }),

  // Contract Audit Log APIs
  getAuditLog: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request('GET', `/audit-log${q ? '?' + q : ''}`);
  },

  // Legacy Approvals & Audit
  listApprovals: () => request('GET', '/approvals'),
  getApproval: (id) => request('GET', `/approvals/${id}`),
  approveRequest: (id) => request('POST', `/approvals/${id}/approve`),
  rejectRequest: (id, reason) => request('POST', `/approvals/${id}/reject`, { reason }),
  listAuditEvents: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return request('GET', `/audit${q ? '?' + q : ''}`);
  },
};

export default api;
