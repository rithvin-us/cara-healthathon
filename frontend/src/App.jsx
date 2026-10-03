import { BrowserRouter, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import Navbar from './components/Navbar';
import { ToastProvider } from './components/Toast';
import { AppProvider, useApp } from './context/AppContext';
import { ROLE_ACCESS } from './lib/access';
import Login from './pages/Login';
import NewDischargePlan from './pages/NewDischargePlan';
import NotFound from './pages/NotFound';
import OutcomesReport from './pages/OutcomesReport';
import PatientDetail from './pages/PatientDetail';
import StaffAdmin from './pages/StaffAdmin';
import Worklist from './pages/Worklist';

function Protected({ roles, children }) {
  const { user } = useApp();
  const location = useLocation();
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  if (roles && !roles.includes(user.role)) return <Navigate to="/worklist" replace />;
  return children;
}

function AppRoutes() {
  const { user } = useApp();
  return (
    <div className="min-h-screen flex flex-col bg-paper font-sans text-ink">
      <Navbar />
      <main className="flex-1">
        <ErrorBoundary>
          <Routes>
            <Route path="/login" element={user ? <Navigate to="/worklist" replace /> : <Login />} />
            <Route path="/worklist" element={<Protected><Worklist /></Protected>} />
            <Route
              path="/new-plan"
              element={<Protected roles={ROLE_ACCESS.newDischarge}><NewDischargePlan /></Protected>}
            />
            <Route path="/patients/:id" element={<Protected><PatientDetail /></Protected>} />
            <Route path="/reports" element={<Protected roles={ROLE_ACCESS.reports}><OutcomesReport /></Protected>} />
            <Route path="/admin" element={<Protected roles={ROLE_ACCESS.staff}><StaffAdmin /></Protected>} />
            <Route path="/" element={<Navigate to={user ? '/worklist' : '/login'} replace />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <AppProvider>
        <ToastProvider>
          <AppRoutes />
        </ToastProvider>
      </AppProvider>
    </BrowserRouter>
  );
}
