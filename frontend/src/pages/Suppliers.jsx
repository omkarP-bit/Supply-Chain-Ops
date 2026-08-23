import React, { useEffect, useState } from 'react';
import api from '../services/api';
import Layout from '../components/Layout';
import { Card, Table, Spinner, Th, Td } from '../components/UI';

export default function Suppliers() {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState('');
  const [filterComponent, setFilterComponent] = useState('ALL');

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        setError(null);
        const data = await api.listSuppliers();
        setSuppliers(data || []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const components = ['ALL', ...Array.from(new Set(suppliers.map((s) => s.component_id || s.material_id).filter(Boolean)))];

  const filtered = suppliers.filter((s) => {
    const nameMatch = (s.supplier_name || s.supplier_id || '').toLowerCase().includes(search.toLowerCase());
    const compMatch = filterComponent === 'ALL' || (s.component_id === filterComponent || s.material_id === filterComponent);
    return nameMatch && compMatch;
  });

  return (
    <Layout>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 18, fontWeight: 700, color: '#12161C', textTransform: 'uppercase', letterSpacing: 0.5 }}>
            Supplier Matrix & Capabilities
          </h1>
          <p style={{ margin: '2px 0 0', fontSize: 12, color: '#8A919B' }}>
            Supplier lead times, quality indices, unit rates & active ISO compliance
          </p>
        </div>
        <input
          type="text"
          placeholder="Filter supplier or ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{
            padding: '6px 12px',
            border: '1px solid #D5D8DC',
            borderRadius: 4,
            fontSize: 12,
            width: 220,
            outline: 'none',
            fontFamily: 'var(--font-mono)',
            background: '#FFFFFF',
          }}
        />
      </div>

      {error && (
        <div style={{ padding: 12, background: '#FFFFFF', color: '#C4302B', borderRadius: 6, marginBottom: 16, border: '1px solid #D5D8DC', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
          [SYSTEM FAULT] {error}
        </div>
      )}

      {/* Component Filter Chips */}
      {components.length > 1 && (
        <div style={{ display: 'flex', gap: 6, marginBottom: 14, flexWrap: 'wrap' }}>
          {components.map((comp) => (
            <button
              key={comp}
              onClick={() => setFilterComponent(comp)}
              style={{
                padding: '5px 10px',
                borderRadius: 4,
                border: '1px solid #D5D8DC',
                background: filterComponent === comp ? '#12161C' : '#FFFFFF',
                color: filterComponent === comp ? '#FFFFFF' : '#3A4149',
                fontSize: 11,
                fontWeight: 600,
                fontFamily: 'var(--font-mono)',
                cursor: 'pointer',
              }}
            >
              {comp === 'ALL' ? 'ALL MATERIALS' : comp}
            </button>
          ))}
        </div>
      )}

      <Card style={{ padding: 18 }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 50, color: '#8A919B', fontFamily: 'var(--font-mono)' }}><Spinner size="lg" /></div>
        ) : filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 30, color: '#8A919B', fontFamily: 'var(--font-mono)', fontSize: 12 }}>
            NO SUPPLIERS MATCH CRITERIA
          </div>
        ) : (
          <Table>
            <thead>
              <tr>
                <Th>Supplier ID</Th>
                <Th>Supplier Name</Th>
                <Th>Material Component</Th>
                <Th>Unit Price</Th>
                <Th>Lead Time</Th>
                <Th>Available Qty</Th>
                <Th>Quality Score</Th>
                <Th>Reliability Score</Th>
                <Th>MOQ</Th>
                <Th>Certifications</Th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((s) => (
                <tr key={`${s.supplier_id}-${s.component_id || s.material_id || ''}`}>
                  <Td><code style={{ fontWeight: 700, color: '#003DA5' }}>{s.supplier_id}</code></Td>
                  <Td style={{ fontWeight: 600 }}>{s.supplier_name}</Td>
                  <Td><code>{s.component_id || s.material_id || 'All Components'}</code></Td>
                  <Td style={{ fontWeight: 600, color: '#12161C', fontFamily: 'var(--font-mono)' }}>
                    INR {Number(s.unit_price || 0).toLocaleString()}
                  </Td>
                  <Td style={{ fontFamily: 'var(--font-mono)' }}>{s.lead_time_days ?? '-'}d</Td>
                  <Td style={{ fontFamily: 'var(--font-mono)' }}>{Number(s.available_quantity || 0).toLocaleString()}u</Td>
                  <Td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                    <span style={{ color: Number(s.quality_score) >= 0.8 || Number(s.quality_score) >= 80 ? '#1E8E5A' : '#B98900' }}>
                      {s.quality_score ? (Number(s.quality_score) > 1 ? Number(s.quality_score).toFixed(1) : `${(Number(s.quality_score) * 100).toFixed(0)}%`) : '-'}
                    </span>
                  </Td>
                  <Td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>
                    <span style={{ color: Number(s.reliability_score || s.overall_reliability_score) >= 0.8 || Number(s.reliability_score || s.overall_reliability_score) >= 80 ? '#1E8E5A' : '#B98900' }}>
                      {s.reliability_score || s.overall_reliability_score ? (Number(s.reliability_score || s.overall_reliability_score) > 1 ? Number(s.reliability_score || s.overall_reliability_score).toFixed(1) : `${(Number(s.reliability_score || s.overall_reliability_score) * 100).toFixed(0)}%`) : '-'}
                    </span>
                  </Td>
                  <Td style={{ fontSize: 12, color: '#8A919B', fontFamily: 'var(--font-mono)' }}>{s.min_order_quantity ? `${s.min_order_quantity}u` : '-'}</Td>
                  <Td>
                    {Array.isArray(s.certifications) && s.certifications.length > 0 ? (
                      <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {s.certifications.map((c) => (
                          <span key={c} style={{ color: '#1E8E5A', fontSize: 10, fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                            ✓ {c}
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span style={{ color: '#8A919B', fontSize: 11, fontFamily: 'var(--font-mono)' }}>STANDARD</span>
                    )}
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
