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
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

const api = {
  health: () => fetch('/health').then(r => r.json()),

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

  getInventory: (materialId) => request('GET', `/inventory/${materialId}`),
  getCoverage: (materialId) => request('GET', `/inventory/${materialId}/coverage`),
  getHistory: (materialId, days = 35) => request('GET', `/inventory/${materialId}/history?days=${days}`),

  listSuppliers: () => request('GET', '/suppliers'),
  getEligibleSuppliers: (materialId, qty) =>
    request('GET', `/suppliers/eligible/${materialId}?required_quantity=${qty}`),
  getSupplier: (id) => request('GET', `/suppliers/${id}`),

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
