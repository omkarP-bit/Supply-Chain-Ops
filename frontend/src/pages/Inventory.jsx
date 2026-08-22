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
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#1e293b' }}>
          Components & Inventory Coverage
        </h1>
        <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: 14 }}>
          Live usable stock, daily consumption rates, safety stock thresholds & warehouse locations
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
        ) : items.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#64748b' }}>No inventory records found.</div>
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
                    <Td><code style={{ fontWeight: 700 }}>{item.component_id}</code></Td>
                    <Td style={{ fontWeight: 600 }}>{item.name}</Td>
                    <Td style={{ color: isBelowSafety ? '#ef4444' : '#0f172a', fontWeight: 600 }}>
                      {item.usable_stock.toLocaleString()}
                    </Td>
                    <Td style={{ color: '#64748b' }}>{item.safety_stock.toLocaleString()}</Td>
                    <Td>{item.daily_usage.toLocaleString()} / day</Td>
                    <Td style={{ fontWeight: 600, color: Number(coverage) < 3 ? '#ef4444' : '#0f172a' }}>
                      {coverage} days
                    </Td>
                    <Td style={{ fontSize: 13, color: '#64748b' }}>{item.warehouse || 'Main WH'}</Td>
                    <Td>
                      {isBelowSafety ? (
                        <span style={{ padding: '3px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700, background: '#fee2e2', color: '#991b1b' }}>
                          BELOW SAFETY
                        </span>
                      ) : (
                        <span style={{ padding: '3px 8px', borderRadius: 4, fontSize: 11, fontWeight: 700, background: '#d1fae5', color: '#065f46' }}>
                          OPTIMAL
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
