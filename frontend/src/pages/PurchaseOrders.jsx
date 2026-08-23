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
      setError(null);
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

  const getPoStatusColor = (status) => {
    if (status === 'delivered') return '#1E8E5A';
    if (status === 'delayed' || status === 'cancelled') return '#C4302B';
    if (status === 'in_transit' || status === 'pending') return '#B98900';
    return '#3A4149';
  };

  return (
    <Layout>
      <div style={{ marginBottom: 16 }}>
        <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#12161C', textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Purchase Orders & Fulfillment
        </h1>
        <p style={{ margin: '2px 0 0', color: '#8A919B', fontSize: 12 }}>
          Fulfillment tracking, concurrency versions & threshold compliance
        </p>
      </div>

      {error && (
        <div style={{ padding: 12, background: '#FFFFFF', color: '#C4302B', borderRadius: 6, marginBottom: 16, border: '1px solid #D5D8DC', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          [SYSTEM FAULT] {error}
        </div>
      )}

      <Card style={{ padding: 18 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 50, color: '#8A919B', fontFamily: 'var(--font-mono)' }}><Spinner size="lg" /></div>
        ) : orders.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 30, color: '#8A919B', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
            NO PURCHASE ORDERS FOUND
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>PO ID</Th>
                <Th>Component</Th>
                <Th>Supplier</Th>
                <Th>Quantity</Th>
                <Th>Total Value</Th>
                <Th>Threshold</Th>
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
                    <Td><code style={{ fontWeight: 700, color: '#003DA5' }}>{po.po_id}</code></Td>
                    <Td><code>{po.component_id}</code></Td>
                    <Td>{po.supplier_id}</Td>
                    <Td style={{ fontFamily: 'var(--font-mono)' }}>{po.quantity.toLocaleString()}u</Td>
                    <Td style={{ fontWeight: 600, color: exceedsThreshold ? '#B98900' : '#12161C', fontFamily: 'var(--font-mono)' }}>
                      INR {Number(po.total_value).toLocaleString()}
                    </Td>
                    <Td style={{ color: '#8A919B', fontFamily: 'var(--font-mono)' }}>
                      INR {Number(po.approval_required_above).toLocaleString()}
                    </Td>
                    <Td style={{ fontSize: 12, color: isDelayed ? '#C4302B' : '#8A919B', fontFamily: 'var(--font-mono)' }}>
                      {new Date(po.expected_delivery).toLocaleDateString()}
                    </Td>
                    <Td>
                      <span
                        style={{
                          fontSize: 11,
                          fontWeight: 700,
                          fontFamily: 'var(--font-mono)',
                          textTransform: 'uppercase',
                          color: getPoStatusColor(po.status),
                        }}
                      >
                        ● {po.status}
                      </span>
                    </Td>
                    <Td style={{ fontSize: 11, color: '#8A919B', fontFamily: 'var(--font-mono)' }}>v{po.version}</Td>
                    <Td>
                      <select
                        value={po.status}
                        disabled={patchingId === po.po_id}
                        onChange={(e) => handleStatusChange(po, e.target.value)}
                        style={{
                          padding: '3px 6px',
                          borderRadius: 4,
                          border: '1px solid #D5D8DC',
                          fontSize: 11,
                          background: '#FFFFFF',
                          fontFamily: 'var(--font-mono)',
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
