import React from 'react';
import { NavLink } from 'react-router-dom';

const navItems = [
  { to: '/dashboard', label: '📊 Alerts Dashboard' },
  { to: '/escalations', label: '⚠️ Escalations Queue' },
  { to: '/audit-log', label: '📜 Audit Trail' },
  { to: '/inventory', label: '📦 Inventory Coverage' },
  { to: '/purchase-orders', label: '📋 Purchase Orders' },
  { to: '/suppliers', label: '🏭 Suppliers' },
  { to: '/incidents', label: '🛡️ Incidents Tower' },
];

const styles = {
  wrapper: { display: 'flex', minHeight: '100vh', fontFamily: "'Segoe UI', system-ui, sans-serif", background: '#f8fafc' },
  sidebar: { width: 230, background: '#0f172a', color: '#fff', padding: '24px 0', flexShrink: 0, display: 'flex', flexDirection: 'column' },
  logo: { padding: '0 20px 20px', fontSize: 16, fontWeight: 700, letterSpacing: 1, borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#38bdf8' },
  badge: { fontSize: 11, background: 'rgba(56,189,248,0.2)', color: '#38bdf8', padding: '2px 6px', borderRadius: 4, marginLeft: 6 },
  nav: { display: 'flex', flexDirection: 'column', gap: 2, padding: '16px 0', flex: 1 },
  link: { display: 'flex', alignItems: 'center', padding: '10px 20px', color: '#94a3b8', textDecoration: 'none', fontSize: 13, fontWeight: 500, borderLeft: '3px solid transparent', transition: 'all 0.15s' },
  activeLink: { color: '#fff', background: 'rgba(255,255,255,0.06)', borderLeftColor: '#38bdf8' },
  main: { flex: 1, padding: 28, overflowY: 'auto' },
};

export default function Layout({ children }) {
  return (
    <div style={styles.wrapper}>
      <aside style={styles.sidebar}>
        <div style={styles.logo}>
          DISRUPTION CONTROL
          <span style={styles.badge}>v2.0</span>
        </div>
        <nav style={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              style={({ isActive }) => ({
                ...styles.link,
                ...(isActive ? styles.activeLink : {}),
              })}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main style={styles.main}>
        {children}
      </main>
    </div>
  );
}
