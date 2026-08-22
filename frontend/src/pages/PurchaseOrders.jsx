import React, { useState, useEffect } from 'react';
import api from '../services/api';
import Layout from '../components/Layout';
import { Card, Button, Spinner, Table, Th, Td } from '../components/UI';

export default function PurchaseOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [patchingId, setPatchingId] = useState(null);
  const [error, setError] = useState(null);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const data = await api.getPurchaseOrders();
      setOrders(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrders();
  }, []);

  const handleStatusChange = async (po, newStatus) => {
    try {
      setPatchingId(po.po_id);
      await api.patchPurchaseOrder(po.po_id, {
        version: po.version,
        status: newStatus,
      });
      await loadOrders();
    } catch (err) {
      alert(`Update failed: ${err.message}`);
    } finally {
      setPatchingId(null);
    }
  };

  return (
    <Layout>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#1e293b' }}>
          Purchase Orders & Fulfillment
        </h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>
          Track procurement orders, optimistic concurrency versioning & approval threshold violations
        </p>
      </div>

      {error && (
        <div style={{ padding: 14, background: '#fee2e2', color: '#991b1b', borderRadius: 8, marginBottom: 20 }}>
          {error}
        </div>
      )}

      <Card style={{ padding: 20 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 60 }}><Spinner size="lg" /></div>
        ) : orders.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#64748b' }}>No purchase orders found.</div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>PO ID</Th>
                <Th>Component</Th>
                <Th>Supplier</Th>
                <Th>Quantity</Th>
                <Th>Total Value</Th>
                <Th>Approval Threshold</Th>
                <Th>Expected Delivery</Th>
                <Th>Status</Th>
                <Th>Version</Th>
                <Th>Actions</Th>
              </tr>
            </thead>
            <tbody>
              {orders.map((po) => {
                const exceedsThreshold = Number(po.total_value) > Number(po.approval_required_above);
                const isDelayed = po.status === 'delayed';
                return (
                  <tr key={po.po_id}>
                    <Td><code style={{ fontWeight: 700 }}>{po.po_id}</code></Td>
                    <Td><code>{po.component_id}</code></Td>
                    <Td>{po.supplier_id}</Td>
                    <Td>{po.quantity.toLocaleString()} units</Td>
                    <Td style={{ fontWeight: 600, color: exceedsThreshold ? '#ef4444' : '#0f172a' }}>
                      INR {Number(po.total_value).toLocaleString()}
                    </Td>
                    <Td style={{ color: '#64748b' }}>
                      INR {Number(po.approval_required_above).toLocaleString()}
                    </Td>
                    <Td style={{ fontSize: 13, color: isDelayed ? '#ef4444' : '#64748b' }}>
                      {new Date(po.expected_delivery).toLocaleDateString()}
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
                            po.status === 'delivered'
                              ? '#d1fae5'
                              : po.status === 'delayed'
                              ? '#fee2e2'
                              : '#fef3c7',
                          color:
                            po.status === 'delivered'
                              ? '#065f46'
                              : po.status === 'delayed'
                              ? '#991b1b'
                              : '#b45309',
                        }}
                      >
                        {po.status}
                      </span>
                    </Td>
                    <Td style={{ fontSize: 12, color: '#64748b' }}>v{po.version}</Td>
                    <Td>
                      <select
                        value={po.status}
                        disabled={patchingId === po.po_id}
                        onChange={(e) => handleStatusChange(po, e.target.value)}
                        style={{
                          padding: '4px 8px',
                          borderRadius: 4,
                          border: '1px solid #cbd5e1',
                          fontSize: 12,
                          background: '#fff',
                        }}
                      >
                        <option value="in_transit">in_transit</option>
                        <option value="delayed">delayed</option>
                        <option value="delivered">delivered</option>
                        <option value="cancelled">cancelled</option>
                      </select>
                    </Td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        )}
      </Card>
    </Layout>
  );
}
