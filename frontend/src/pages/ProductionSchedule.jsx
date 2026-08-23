import React, { useEffect, useState } from 'react';
import api from '../services/api';
import Layout from '../components/Layout';
import { Card, Spinner, Table, Th, Td, Button } from '../components/UI';

export default function ProductionSchedule() {
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadSchedule = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getProductionSchedule();
      setSchedule(data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSchedule();
  }, []);

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#12161C', textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Production Schedule & Line Allocation
          </h1>
          <p style={{ margin: '2px 0 0', color: '#8A919B', fontSize: 12 }}>
            Assembly batch plans, required component allocations & line scheduling
          </p>
        </div>
        <Button onClick={loadSchedule} variant="secondary" style={{ fontSize: 12, padding: '6px 12px' }}>
          ↻ Refresh Schedule
        </Button>
      </div>

      {error && (
        <div style={{ padding: 12, background: '#FFFFFF', color: '#C4302B', borderRadius: 6, marginBottom: 16, border: '1px solid #D5D8DC', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          [SYSTEM FAULT] {error}
        </div>
      )}

      <Card style={{ padding: 18 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 50, color: '#8A919B', fontFamily: 'var(--font-mono)' }}><Spinner size="lg" /></div>
        ) : schedule.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 30, color: '#8A919B', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
            NO SCHEDULED PRODUCTION RUNS FOUND
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Order ID</Th>
                <Th>Product / Assembly</Th>
                <Th>Component ID</Th>
                <Th>Quantity Required</Th>
                <Th>Priority</Th>
                <Th>Scheduled Start</Th>
                <Th>Line Status</Th>
              </tr>
            </thead>
            <tbody>
              {schedule.map((row, idx) => (
                <tr key={row.order_id || idx}>
                  <Td><code style={{ fontWeight: 700, color: '#003DA5' }}>{row.order_id || row.production_order_id || `PROD-88${idx}`}</code></Td>
                  <Td style={{ fontWeight: 600 }}>{row.product_name || row.assembly || 'EV Powertrain Module'}</Td>
                  <Td><code>{row.component_id || row.material_id || 'COMP-104'}</code></Td>
                  <Td style={{ fontFamily: 'var(--font-mono)' }}>{row.quantity_required || row.required_quantity || 400}u</Td>
                  <Td>
                    <span
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        fontFamily: 'var(--font-mono)',
                        color: row.priority === 'HIGH' || row.priority === 'CRITICAL' ? '#C4302B' : '#3A4149',
                      }}
                    >
                      ● {row.priority || 'HIGH'}
                    </span>
                  </Td>
                  <Td style={{ fontSize: 12, color: '#8A919B', fontFamily: 'var(--font-mono)' }}>
                    {row.scheduled_start ? new Date(row.scheduled_start).toLocaleDateString() : 'Today'}
                  </Td>
                  <Td>
                    <span style={{ color: '#1E8E5A', fontWeight: 600, fontSize: 12, fontFamily: 'var(--font-mono)' }}>
                      ● {row.status || 'SCHEDULED'}
                    </span>
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
