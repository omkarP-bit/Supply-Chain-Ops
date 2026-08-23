import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Approvals from './pages/Approvals';
import AuditTrail from './pages/AuditTrail';
import Inventory from './pages/Inventory';
import PurchaseOrders from './pages/PurchaseOrders';
import Suppliers from './pages/Suppliers';
import Incidents from './pages/Incidents';
import IncidentDetails from './pages/IncidentDetails';
import ProductionSchedule from './pages/ProductionSchedule';
import Inbox from './pages/Inbox';
import ScenarioLab from './pages/ScenarioLab';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<Dashboard />} />
      <Route path="/inbox" element={<Inbox />} />
      <Route path="/scenario-lab" element={<ScenarioLab />} />
      <Route path="/scenarios" element={<ScenarioLab />} />
      <Route path="/incidents" element={<Incidents />} />
      <Route path="/incidents/:id" element={<IncidentDetails />} />
      <Route path="/audit-log" element={<AuditTrail />} />
      <Route path="/audit" element={<AuditTrail />} />
      <Route path="/inventory" element={<Inventory />} />
      <Route path="/purchase-orders" element={<PurchaseOrders />} />
      <Route path="/suppliers" element={<Suppliers />} />
      <Route path="/production-schedule" element={<ProductionSchedule />} />
      <Route path="/escalations" element={<Approvals />} />
      <Route path="/approvals" element={<Approvals />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
