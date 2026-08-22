import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Incidents from './pages/Incidents';
import IncidentDetails from './pages/IncidentDetails';
import Suppliers from './pages/Suppliers';
import Approvals from './pages/Approvals';
import AuditTrail from './pages/AuditTrail';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/incidents" element={<Incidents />} />
      <Route path="/incidents/:id" element={<IncidentDetails />} />
      <Route path="/suppliers" element={<Suppliers />} />
      <Route path="/approvals" element={<Approvals />} />
      <Route path="/audit" element={<AuditTrail />} />
    </Routes>
  );
}
