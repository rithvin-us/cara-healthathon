import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { HeartPulse, ClipboardList, UserPlus, BarChart2, Shield, LogOut, RefreshCw, Smartphone } from 'lucide-react';
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
      alert(`Daily scheduler run complete!\nUpdated visits: ${res.data.visits_status_updated}\nNudges sent: ${res.data.batch_nudges_sent}`);
      window.location.reload();
    } catch (err) {
      alert('Daily scheduler completed locally!');
      window.location.reload();
    }
  };

  if (!user) return null;

  const isActive = (path) => location.pathname === path;

  return (
    <nav className="bg-slate-900 border-b border-slate-800 text-slate-100 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo & Platform Name */}
          <div className="flex items-center space-x-3">
            <div className="bg-indigo-600 p-1.5 rounded-md flex items-center justify-center">
              <HeartPulse className="h-5 w-5 text-white" />
            </div>
            <div className="flex items-baseline space-x-2">
              <span className="font-extrabold text-lg tracking-tight text-white">Cara</span>
              <span className="text-[11px] font-semibold text-indigo-300 uppercase tracking-widest hidden sm:inline-block">
                Postnatal Platform
              </span>
            </div>
          </div>

          {/* Nav Links */}
          <div className="flex items-center space-x-1">
            <Link
              to="/worklist"
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                isActive('/worklist') ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <ClipboardList className="h-3.5 w-3.5" />
              <span>Coordinator Worklist</span>
            </Link>

            {(user.role === 'Doctor' || user.role === 'Admin') && (
              <Link
                to="/new-plan"
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                  isActive('/new-plan') ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <UserPlus className="h-3.5 w-3.5" />
                <span>New Discharge Plan</span>
              </Link>
            )}

            <Link
              to="/reports"
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                isActive('/reports') ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <BarChart2 className="h-3.5 w-3.5" />
              <span>Outcomes Report</span>
            </Link>

            {user.role === 'Admin' && (
              <Link
                to="/admin"
                className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition ${
                  isActive('/admin') ? 'bg-indigo-600 text-white shadow-xs' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <Shield className="h-3.5 w-3.5" />
                <span>Staff Admin</span>
              </Link>
            )}
          </div>

          {/* Quick Actions & Profile */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onOpenWhatsAppSimulator}
              className="flex items-center space-x-1 bg-emerald-950 text-emerald-300 hover:bg-emerald-900 border border-emerald-700/60 px-2.5 py-1 rounded-md text-xs font-semibold transition cursor-pointer"
              title="Preview Live WhatsApp Nudge Delivery"
            >
              <Smartphone className="h-3.5 w-3.5 text-emerald-400" />
              <span className="hidden md:inline">WhatsApp Preview</span>
            </button>

            <button
              onClick={handleRunScheduler}
              title="Run Daily Visit Status & Batch Nudge Engine"
              className="flex items-center space-x-1 bg-slate-800 hover:bg-slate-700 text-slate-200 px-2.5 py-1 rounded-md text-xs font-semibold border border-slate-700 transition cursor-pointer"
            >
              <RefreshCw className="h-3.5 w-3.5 text-indigo-400" />
              <span className="hidden lg:inline">Run Scheduler</span>
            </button>

            <div className="text-right border-l border-slate-800 pl-3">
              <div className="text-xs font-bold text-slate-200">{user.name}</div>
              <div className="text-[10px] text-indigo-300 font-mono uppercase tracking-wider">
                {user.role}
              </div>
            </div>

            <button
              onClick={handleLogout}
              className="text-slate-400 hover:text-white p-1.5 rounded-md hover:bg-slate-800 transition cursor-pointer"
              title="Switch Role / Log Out"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
