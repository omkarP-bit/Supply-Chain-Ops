import React, { useState, useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

const styles = {
  wrapper: { display: 'flex', minHeight: '100vh', fontFamily: "var(--font-body)", background: 'var(--bg-base)' },
  sidebar: { width: 235, background: '#12161C', color: '#D5D8DC', padding: '24px 0', flexShrink: 0, display: 'flex', flexDirection: 'column', borderRight: '1px solid #1E242C' },
  logo: { padding: '0 20px 20px', fontSize: 16, fontWeight: 700, letterSpacing: -0.2, borderBottom: '1px solid #1E242C', color: '#FFFFFF', display: 'flex', alignItems: 'center', justifyContent: 'space-between' },
  brandBadge: { fontSize: 10, background: 'transparent', color: '#003DA5', border: '1px solid #003DA5', padding: '1px 5px', borderRadius: 4, fontWeight: 700, fontFamily: 'var(--font-mono)' },
  nav: { display: 'flex', flexDirection: 'column', gap: 2, padding: '16px 0', flex: 1 },
  link: { display: 'flex', alignItems: 'center', padding: '9px 20px', color: '#8A919B', textDecoration: 'none', fontSize: 13, fontWeight: 500, borderLeft: '3px solid transparent', transition: 'all 0.15s', cursor: 'pointer' },
  activeLink: { color: '#FFFFFF', background: '#1E242C', borderLeftColor: '#003DA5', fontWeight: 600 },
  expandHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '9px 20px', color: '#8A919B', fontSize: 13, fontWeight: 500, borderLeft: '3px solid transparent', cursor: 'pointer', userSelect: 'none', transition: 'all 0.15s' },
  submenu: { display: 'flex', flexDirection: 'column', gap: 1, background: '#1E242C', padding: '4px 0 4px 12px', borderLeft: '1px solid #3A4149', margin: '4px 16px 8px 20px' },
  subLink: { display: 'flex', alignItems: 'center', padding: '7px 12px', color: '#8A919B', textDecoration: 'none', fontSize: 12, fontWeight: 500, borderRadius: 4, transition: 'all 0.15s' },
  activeSubLink: { color: '#FFFFFF', fontWeight: 600, borderLeft: '2px solid #003DA5' },
  main: { flex: 1, padding: 28, overflowY: 'auto', maxWidth: 'calc(100vw - 235px)', background: '#F4F5F7' },
};

export default function Layout({ children }) {
  const location = useLocation();
  const isResourceRoute = ['/inventory', '/purchase-orders', '/suppliers'].some(p => location.pathname.startsWith(p));
  const [resourcesOpen, setResourcesOpen] = useState(isResourceRoute || true);

  useEffect(() => {
    if (isResourceRoute) {
      setResourcesOpen(true);
    }
  }, [location.pathname]);

  return (
    <div style={styles.wrapper}>
      <aside style={styles.sidebar}>
        <div style={styles.logo}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: '#003DA5', fontWeight: 900, fontSize: 18 }}>■</span>
            <span>Syntra AI</span>
          </div>
          <span style={styles.brandBadge}>TATA OPS</span>
        </div>

        <nav style={styles.nav}>
          {/* 1. Inbox */}
          <NavLink
            to="/inbox"
            style={({ isActive }) => ({
              ...styles.link,
              ...(isActive || location.pathname.startsWith('/incidents') ? styles.activeLink : {}),
            })}
          >
            <span style={{ marginRight: 10, color: '#8A919B' }}>✉</span> Inbox
          </NavLink>

          {/* 2. Homepage */}
          <NavLink
            to="/dashboard"
            style={({ isActive }) => ({
              ...styles.link,
              ...(isActive ? styles.activeLink : {}),
            })}
          >
            <span style={{ marginRight: 10, color: '#8A919B' }}>⌂</span> Homepage
          </NavLink>

          {/* 3. Audit Trail */}
          <NavLink
            to="/audit-log"
            style={({ isActive }) => ({
              ...styles.link,
              ...(isActive || location.pathname.startsWith('/audit') ? styles.activeLink : {}),
            })}
          >
            <span style={{ marginRight: 10, color: '#8A919B' }}>≡</span> Audit Trail
          </NavLink>

          {/* 4. Resources (Expandable Submenu) */}
          <div>
            <div
              onClick={() => setResourcesOpen(!resourcesOpen)}
              style={{
                ...styles.expandHeader,
                ...(isResourceRoute ? { color: '#FFFFFF', fontWeight: 600 } : {}),
              }}
            >
              <span><span style={{ marginRight: 10, color: '#8A919B' }}>⊞</span> Resources</span>
              <span style={{ fontSize: 10, color: '#8A919B', transition: 'transform 0.2s', transform: resourcesOpen ? 'rotate(90deg)' : 'none' }}>
                ▸
              </span>
            </div>

            {resourcesOpen && (
              <div style={styles.submenu}>
                <NavLink
                  to="/inventory"
                  style={({ isActive }) => ({
                    ...styles.subLink,
                    ...(isActive ? styles.activeSubLink : {}),
                  })}
                >
                  Inventory
                </NavLink>
                <NavLink
                  to="/purchase-orders"
                  style={({ isActive }) => ({
                    ...styles.subLink,
                    ...(isActive ? styles.activeSubLink : {}),
                  })}
                >
                  Purchase Orders
                </NavLink>
                <NavLink
                  to="/suppliers"
                  style={({ isActive }) => ({
                    ...styles.subLink,
                    ...(isActive ? styles.activeSubLink : {}),
                  })}
                >
                  Supplier Catalog
                </NavLink>
              </div>
            )}
          </div>

          {/* 5. Production Schedule */}
          <NavLink
            to="/production-schedule"
            style={({ isActive }) => ({
              ...styles.link,
              ...(isActive ? styles.activeLink : {}),
            })}
          >
            <span style={{ marginRight: 10, color: '#8A919B' }}>▦</span> Production Schedule
          </NavLink>

          {/* 6. Scenario Lab */}
          <NavLink
            to="/scenario-lab"
            style={({ isActive }) => ({
              ...styles.link,
              ...(isActive || location.pathname.startsWith('/scenario') ? styles.activeLink : {}),
            })}
          >
            <span style={{ marginRight: 10, color: '#8A919B' }}>◈</span> Scenario Lab
          </NavLink>
        </nav>
      </aside>

      <main style={styles.main}>
        {children}
      </main>
    </div>
  );
}
