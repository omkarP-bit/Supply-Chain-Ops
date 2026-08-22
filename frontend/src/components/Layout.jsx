import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';

const navItems = [
  { to: '/', label: 'Dashboard' },
  { to: '/incidents', label: 'Incidents' },
  { to: '/suppliers', label: 'Suppliers' },
  { to: '/approvals', label: 'Approvals' },
  { to: '/audit', label: 'Audit Trail' },
];

const styles = {
  wrapper: { display: 'flex', minHeight: '100vh', fontFamily: "'Segoe UI', system-ui, sans-serif", background: '#f0f2f5' },
  sidebar: { width: 220, background: '#1a1a2e', color: '#fff', padding: '24px 0', flexShrink: 0, display: 'flex', flexDirection: 'column' },
  logo: { padding: '0 20px 24px', fontSize: 16, fontWeight: 700, letterSpacing: 1, borderBottom: '1px solid rgba(255,255,255,0.1)' },
  nav: { display: 'flex', flexDirection: 'column', gap: 2, padding: '16px 0', flex: 1 },
  link: { display: 'block', padding: '10px 20px', color: 'rgba(255,255,255,0.7)', textDecoration: 'none', fontSize: 14, fontWeight: 500, borderLeft: '3px solid transparent', transition: 'all 0.15s' },
  activeLink: { color: '#fff', background: 'rgba(255,255,255,0.08)', borderLeftColor: '#4fc3f7' },
  main: { flex: 1, padding: 24, overflowY: 'auto' },
  title: { margin: '0 0 20px', fontSize: 22, fontWeight: 700, color: '#1a1a2e' },
};

export default function Layout({ children }) {
  return (
    <div style={styles.wrapper}>
      <aside style={styles.sidebar}>
        <div style={styles.logo}>SC OPS</div>
        <nav style={styles.nav}>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
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
