import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Worklist from './pages/Worklist';
import NewDischargePlan from './pages/NewDischargePlan';
import PatientDetail from './pages/PatientDetail';
import OutcomesReport from './pages/OutcomesReport';
import StaffAdmin from './pages/StaffAdmin';
import WhatsAppPreviewModal from './components/WhatsAppPreviewModal';

function ProtectedRoute({ user, allowedRoles, children }) {
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/worklist" replace />;
  }
  return children;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [globalWhatsAppOpen, setGlobalWhatsAppOpen] = useState(false);

  useEffect(() => {
    const savedUser = localStorage.getItem('cara_user');
    const savedToken = localStorage.getItem('cara_token');
    if (savedUser && savedToken) {
      try {
        setUser(JSON.parse(savedUser));
      } catch (e) {
        localStorage.removeItem('cara_user');
        localStorage.removeItem('cara_token');
      }
    }
    setLoading(false);
  }, []);

  if (loading) return null;

  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col bg-paper font-sans text-ink">
        <Navbar
          user={user}
          setUser={setUser}
          onOpenWhatsAppSimulator={() => setGlobalWhatsAppOpen(true)}
        />

        <main className="flex-1">
          <Routes>
            <Route path="/login" element={<Login setUser={setUser} />} />

            <Route
              path="/worklist"
              element={
                <ProtectedRoute user={user}>
                  <Worklist />
                </ProtectedRoute>
              }
            />

            <Route
              path="/new-plan"
              element={
                <ProtectedRoute user={user} allowedRoles={['Doctor', 'Admin']}>
                  <NewDischargePlan />
                </ProtectedRoute>
              }
            />

            <Route
              path="/patients/:id"
              element={
                <ProtectedRoute user={user}>
                  <PatientDetail />
                </ProtectedRoute>
              }
            />

            <Route
              path="/reports"
              element={
                <ProtectedRoute user={user}>
                  <OutcomesReport />
                </ProtectedRoute>
              }
            />

            <Route
              path="/admin"
              element={
                <ProtectedRoute user={user} allowedRoles={['Admin']}>
                  <StaffAdmin />
                </ProtectedRoute>
              }
            />

            <Route path="*" element={<Navigate to={user ? "/worklist" : "/login"} replace />} />
          </Routes>
        </main>

        <WhatsAppPreviewModal
          isOpen={globalWhatsAppOpen}
          onClose={() => setGlobalWhatsAppOpen(false)}
          patientName="Sunita Rao"
          recipientContact="+919876543210"
          visitType="24h PNC Checkup"
          dueDate="Tomorrow (10:00 AM)"
          facilityName="City Maternity Hospital"
          language="Hindi"
        />
      </div>
    </BrowserRouter>
  );
}
