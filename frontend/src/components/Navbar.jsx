import { useState } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { adminApi, errorMessage } from '../api/client';
import { useApp } from '../context/AppContext';
import { can } from '../lib/access';
import { useToast } from './Toast';

const ROLE_NAMES = { Doctor: 'Doctor', Coordinator: 'Nurse coordinator', Admin: 'Hospital admin' };

export default function Navbar() {
  const { user, signOut, refreshData, health } = useApp();
  const toast = useToast();
  const navigate = useNavigate();
  const location = useLocation();
  const [running, setRunning] = useState(false);

  if (!user || location.pathname === '/login') return null;

  const handleSignOut = () => {
    signOut();
    navigate('/login');
  };

  const handleRunDailyJob = async () => {
    setRunning(true);
    try {
      const { data } = await adminApi.runDailyJob();
      const sent = data.batch_nudges_sent;
      toast.success(
        sent === 0
          ? 'Daily update done. Everyone due today has already been reminded.'
          : `Daily update done. ${sent} WhatsApp ${sent === 1 ? 'reminder' : 'reminders'} sent.`,
      );
      refreshData();
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't run the daily update."));
    } finally {
      setRunning(false);
    }
  };

  const tab = ({ isActive }) =>
    `flex items-center whitespace-nowrap text-sm font-semibold border-b-2 ${
      isActive ? 'border-scrub text-ink' : 'border-transparent text-ink-soft hover:text-ink'
    }`;

  return (
    <nav className="bg-white border-b border-rule sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-stretch justify-between gap-6 h-14">
          <div className="flex items-center gap-3 shrink-0">
            <img src="/favicon.svg" alt="" className="h-6 w-6" />
            <span className="text-lg font-bold text-scrub">Cara</span>
            <span className="text-sm text-ink-soft hidden lg:inline">{user.facility_name}</span>
          </div>

          <div className="flex items-stretch gap-6 flex-1 min-w-0 overflow-x-auto no-scrollbar">
            <NavLink to="/worklist" className={tab}>
              Follow-ups
            </NavLink>
            {can(user, 'newDischarge') && (
              <NavLink to="/new-plan" className={tab}>
                New discharge
              </NavLink>
            )}
            {can(user, 'reports') && (
              <NavLink to="/reports" className={tab}>
                Reports
              </NavLink>
            )}
            {can(user, 'staff') && (
              <NavLink to="/admin" className={tab}>
                Staff
              </NavLink>
            )}
          </div>

          <div className="flex items-center gap-4 shrink-0">
            {health?.nudge_provider === 'simulated' && (
              <span
                className="hidden md:inline text-xs font-semibold text-soon bg-soon-tint rounded px-2 py-1"
                title="Messages are composed and logged but not sent to real phones"
              >
                Demo messaging
              </span>
            )}
            <button
              type="button"
              onClick={handleRunDailyJob}
              disabled={running}
              title="Update visit statuses and send today's WhatsApp reminders"
              className="btn-link whitespace-nowrap"
            >
              {running ? 'Running…' : 'Run daily update'}
            </button>

            <div className="text-right border-l border-rule pl-4 hidden sm:block">
              <div className="text-sm font-semibold text-ink">{user.name}</div>
              <div className="text-xs text-ink-faint">{ROLE_NAMES[user.role] || user.role}</div>
            </div>

            <button
              type="button"
              onClick={handleSignOut}
              className="text-sm font-semibold text-ink-soft hover:text-ink whitespace-nowrap"
            >
              Sign out
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
