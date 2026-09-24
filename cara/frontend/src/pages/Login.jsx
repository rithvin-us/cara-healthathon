import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/client';
import { HeartPulse, Stethoscope, ClipboardList, Shield, ArrowRight, Activity, Hospital, Lock } from 'lucide-react';

export default function Login({ setUser }) {
  const [loadingRole, setLoadingRole] = useState('');
  const navigate = useNavigate();

  const handleOneClickLogin = async (role) => {
    setLoadingRole(role);
    try {
      const res = await authApi.quickLogin(role);
      const data = res.data;
      localStorage.setItem('cara_token', data.access_token);
      const userObj = {
        user_id: data.user_id,
        name: data.name,
        role: data.role,
        facility_id: data.facility_id,
      };
      localStorage.setItem('cara_user', JSON.stringify(userObj));
      setUser(userObj);
      navigate('/worklist');
    } catch (err) {
      // Failsafe local demo session
      const nameMap = {
        Doctor: 'Dr. Ananya Sharma (OBGYN)',
        Coordinator: 'Priya Patel (Lactation Counselor)',
        Admin: 'Rajesh Kumar (Facility Admin)',
      };
      const userObj = {
        user_id: 1,
        name: nameMap[role] || `${role} User`,
        role: role,
        facility_id: 1,
      };
      localStorage.setItem('cara_token', 'demo_token_cara_2026');
      localStorage.setItem('cara_user', JSON.stringify(userObj));
      setUser(userObj);
      navigate('/worklist');
    } finally {
      setLoadingRole('');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 font-sans antialiased text-slate-100">
      <div className="sm:mx-auto sm:w-full sm:max-w-xl text-center space-y-3">
        <div className="inline-flex items-center justify-center bg-indigo-600 p-3 rounded-2xl shadow-lg ring-4 ring-indigo-500/20">
          <HeartPulse className="h-8 w-8 text-white" />
        </div>
        <h1 className="text-3xl font-black tracking-tight text-white">
          Cara Clinical Portal
        </h1>
        <p className="text-xs text-slate-400 font-medium max-w-md mx-auto">
          Postnatal Follow-Up Coordination System • Health-a-thon 2026 Maternal Track
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-xl">
        <div className="bg-slate-950 p-8 rounded-2xl shadow-2xl border border-slate-800 space-y-6">
          <div className="flex items-center justify-between border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">Select Hospital Role</h2>
              <p className="text-xs text-slate-400">One-click role access for demonstration</p>
            </div>
            <span className="flex items-center text-[10px] text-emerald-400 font-mono bg-emerald-950/80 px-2.5 py-1 rounded border border-emerald-800">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mr-1.5 animate-pulse"></span>
              Live Demo Sandbox
            </span>
          </div>

          <div className="space-y-3">
            {/* OBGYN Doctor Card */}
            <button
              type="button"
              onClick={() => handleOneClickLogin('Doctor')}
              disabled={!!loadingRole}
              className="w-full p-4 rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-850 hover:border-indigo-500/60 transition text-left flex items-center justify-between group cursor-pointer"
            >
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-indigo-950 text-indigo-400 rounded-xl border border-indigo-800/60 group-hover:scale-105 transition">
                  <Stethoscope className="h-6 w-6" />
                </div>
                <div>
                  <div className="font-bold text-slate-100 text-sm flex items-center space-x-2">
                    <span>OBGYN Doctor</span>
                    <span className="text-[10px] font-bold bg-indigo-950 text-indigo-300 px-2 py-0.5 rounded border border-indigo-800">
                      Discharge Planning
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Set discharge dates, FOGSI Gestosis risk flags & weekly interval overrides
                  </div>
                </div>
              </div>
              <div className="text-indigo-400 text-xs font-semibold flex items-center">
                <span>{loadingRole === 'Doctor' ? 'Opening...' : 'Select Role'}</span>
                <ArrowRight className="h-4 w-4 ml-1.5 group-hover:translate-x-1 transition" />
              </div>
            </button>

            {/* Coordinator Card */}
            <button
              type="button"
              onClick={() => handleOneClickLogin('Coordinator')}
              disabled={!!loadingRole}
              className="w-full p-4 rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-850 hover:border-teal-500/60 transition text-left flex items-center justify-between group cursor-pointer"
            >
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-teal-950 text-teal-400 rounded-xl border border-teal-800/60 group-hover:scale-105 transition">
                  <ClipboardList className="h-6 w-6" />
                </div>
                <div>
                  <div className="font-bold text-slate-100 text-sm flex items-center space-x-2">
                    <span>Facility Coordinator</span>
                    <span className="text-[10px] font-bold bg-teal-950 text-teal-300 px-2 py-0.5 rounded border border-teal-800">
                      Nurse Worklist
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Track ranked overdue patients, record visit completion & send WhatsApp nudges
                  </div>
                </div>
              </div>
              <div className="text-teal-400 text-xs font-semibold flex items-center">
                <span>{loadingRole === 'Coordinator' ? 'Opening...' : 'Select Role'}</span>
                <ArrowRight className="h-4 w-4 ml-1.5 group-hover:translate-x-1 transition" />
              </div>
            </button>

            {/* Admin Card */}
            <button
              type="button"
              onClick={() => handleOneClickLogin('Admin')}
              disabled={!!loadingRole}
              className="w-full p-4 rounded-xl border border-slate-800 bg-slate-900/80 hover:bg-slate-850 hover:border-purple-500/60 transition text-left flex items-center justify-between group cursor-pointer"
            >
              <div className="flex items-center space-x-4">
                <div className="p-3 bg-purple-950 text-purple-400 rounded-xl border border-purple-800/60 group-hover:scale-105 transition">
                  <Shield className="h-6 w-6" />
                </div>
                <div>
                  <div className="font-bold text-slate-100 text-sm flex items-center space-x-2">
                    <span>Facility Administrator</span>
                    <span className="text-[10px] font-bold bg-purple-950 text-purple-300 px-2 py-0.5 rounded border border-purple-800">
                      Outcomes & Audit
                    </span>
                  </div>
                  <div className="text-xs text-slate-400 mt-1">
                    Manage staff, generate due-vs-completed outcomes reports & AI weekly digests
                  </div>
                </div>
              </div>
              <div className="text-purple-400 text-xs font-semibold flex items-center">
                <span>{loadingRole === 'Admin' ? 'Opening...' : 'Select Role'}</span>
                <ArrowRight className="h-4 w-4 ml-1.5 group-hover:translate-x-1 transition" />
              </div>
            </button>
          </div>

          <div className="pt-2 text-center border-t border-slate-800/80">
            <span className="text-[11px] text-slate-500 flex items-center justify-center">
              <Hospital className="h-3.5 w-3.5 mr-1 text-slate-400" />
              Target Facility: City Maternity & Children's Hospital (Mumbai)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
