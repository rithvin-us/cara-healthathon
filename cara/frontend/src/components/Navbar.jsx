import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { adminApi } from '../api/client';

export default function Navbar({ user, setUser, onOpenWhatsAppSimulator }) {
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    localStorage.removeItem('cara_token');
    localStorage.removeItem('cara_user');
    setUser(null);
    navigate('/login');
  };

  const handleRunScheduler = async () => {
    try {
      const res = await adminApi.triggerScheduler();
      alert(`Daily update done. ${res.data.visits_status_updated} visits updated, ${res.data.batch_nudges_sent} reminders sent.`);
      window.location.reload();
    } catch (err) {
      alert('Daily update done on this device.');
      window.location.reload();
    }
  };

  if (!user || location.pathname === '/login') return null;

  const isActive = (path) => location.pathname === path;

  const tabClass = (path) =>
    `flex items-center whitespace-nowrap text-sm font-semibold border-b-2 ${
      isActive(path) ? 'border-scrub text-ink' : 'border-transparent text-ink-soft hover:text-ink'
    }`;

  return (
    <nav className="bg-white border-b border-rule sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-stretch justify-between gap-6 h-14">
          <div className="flex items-center gap-3 shrink-0">
            <span className="text-lg font-bold text-scrub">Cara</span>
            <span className="text-sm text-ink-soft hidden md:inline">City Maternity Hospital</span>
          </div>

          <div className="flex items-stretch gap-6 flex-1 min-w-0 overflow-x-auto no-scrollbar">
            <Link to="/worklist" className={tabClass('/worklist')}>
              Follow-ups
            </Link>

            {(user.role === 'Doctor' || user.role === 'Admin') && (
              <Link to="/new-plan" className={tabClass('/new-plan')}>
                New discharge
              </Link>
            )}

            <Link to="/reports" className={tabClass('/reports')}>
              Reports
            </Link>

            {user.role === 'Admin' && (
              <Link to="/admin" className={tabClass('/admin')}>
                Staff
              </Link>
            )}
          </div>

          <div className="flex items-center gap-4 shrink-0">
            <button
              onClick={onOpenWhatsAppSimulator}
              className="text-scrub text-sm font-semibold whitespace-nowrap hover:underline underline-offset-2 cursor-pointer"
              title="See the WhatsApp message a mother receives"
            >
              Preview message
            </button>

            <button
              onClick={handleRunScheduler}
              title="Update visit statuses and send today's reminders"
              className="text-scrub text-sm font-semibold whitespace-nowrap hover:underline underline-offset-2 cursor-pointer"
            >
              Run daily update
            </button>

            <div className="text-right border-l border-rule pl-4 hidden sm:block">
              <div className="text-sm font-semibold text-ink">{user.name.split(' (')[0]}</div>
              <div className="text-xs text-ink-faint">{user.role}</div>
            </div>

            <button
              onClick={handleLogout}
              className="text-sm font-semibold text-ink-soft hover:text-ink whitespace-nowrap cursor-pointer"
              title="Sign out or switch user"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
