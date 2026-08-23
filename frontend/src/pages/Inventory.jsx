import React, { useState, useEffect } from 'react';
import api from '../services/api';
import Layout from '../components/Layout';
import { Card, Spinner, Table, Th, Td } from '../components/UI';

export default function Inventory() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await api.getInventory();
        setItems(data || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <Layout>
      <div style={{ marginBottom: 16 }}>
        <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#12161C', textTransform: 'uppercase', letterSpacing: 0.5 }}>
          Components & Inventory Matrix
        </h1>
        <p style={{ margin: '2px 0 0', color: '#8A919B', fontSize: 12 }}>
          Live telemetry of usable stock, daily consumption burn rates & safety thresholds
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
        ) : items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 30, color: '#8A919B', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
            NO INVENTORY DATA LOGGED
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Component ID</Th>
                <Th>Name</Th>
                <Th>Usable Stock</Th>
                <Th>Safety Stock</Th>
                <Th>Daily Usage</Th>
                <Th>Coverage (Days)</Th>
                <Th>Warehouse</Th>
                <Th>Status</Th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const coverage = item.daily_usage > 0 ? (item.usable_stock / item.daily_usage).toFixed(1) : '∞';
                const isBelowSafety = item.usable_stock < item.safety_stock;
                return (
                  <tr key={item.component_id}>
                    <Td><code style={{ fontWeight: 700, color: '#003DA5' }}>{item.component_id}</code></Td>
                    <Td style={{ fontWeight: 600 }}>{item.name}</Td>
                    <Td style={{ color: isBelowSafety ? '#C4302B' : '#12161C', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                      {item.usable_stock.toLocaleString()}u
                    </Td>
                    <Td style={{ color: '#8A919B', fontFamily: 'var(--font-mono)' }}>{item.safety_stock.toLocaleString()}u</Td>
                    <Td style={{ fontFamily: 'var(--font-mono)' }}>{item.daily_usage.toLocaleString()} / day</Td>
                    <Td style={{ fontWeight: 600, color: Number(coverage) < 3 ? '#C4302B' : '#12161C', fontFamily: 'var(--font-mono)' }}>
                      {coverage} days
                    </Td>
                    <Td style={{ fontSize: 12, color: '#8A919B' }}>{item.warehouse || 'WH-MAIN'}</Td>
                    <Td>
                      {isBelowSafety ? (
                        <span style={{ fontSize: 11, fontWeight: 700, color: '#C4302B', fontFamily: 'var(--font-mono)' }}>
                          ● BELOW SAFETY
                        </span>
                      ) : (
                        <span style={{ fontSize: 11, fontWeight: 700, color: '#1E8E5A', fontFamily: 'var(--font-mono)' }}>
                          ● OPTIMAL
                        </span>
                      )}
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
