import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from '../api/client';

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
    <div className="min-h-screen bg-paper antialiased text-ink lg:flex">
      <div className="lg:w-1/2 lg:h-screen lg:sticky lg:top-0">
        <img
          src="/images/family-newborn.jpg"
          alt="Parents smiling at their sleeping newborn"
          width="1100"
          height="1650"
          loading="eager"
          decoding="async"
          className="block h-56 sm:h-72 w-full object-cover object-[center_25%] lg:h-full lg:object-[center_8%]"
        />
      </div>

      <div className="bg-paper lg:w-1/2 lg:min-h-screen flex items-center py-10 px-4 sm:px-6 lg:px-12">
        <div className="w-full max-w-md mx-auto">
        <div>
          <div className="text-scrub font-bold text-xl">Cara</div>
          <h1 className="text-3xl font-bold text-ink leading-tight mt-6">
            Postnatal follow-up for City Maternity & Children's Hospital
          </h1>
          <p className="text-sm text-ink-soft mt-4">
            Every mother discharged here gets checkups at 24 hours, 3 days, 2 weeks and 6 weeks. Cara keeps track of who is due and reminds families on WhatsApp.
          </p>
        </div>

        <div className="bg-white border border-rule rounded-md mt-8">
          <div className="px-5 py-4">
            <h2 className="text-base font-bold text-ink">Sign in to the demo</h2>
            <p className="text-sm text-ink-soft mt-1">Choose a role. These are test accounts with made-up patients.</p>
          </div>

          <button
            type="button"
            onClick={() => handleOneClickLogin('Doctor')}
            disabled={!!loadingRole}
            className="w-full px-5 py-4 border-t border-rule text-left flex items-center justify-between gap-4 hover:bg-paper cursor-pointer disabled:cursor-default"
          >
            <div>
              <div className="text-sm font-semibold text-ink">Doctor</div>
              <div className="text-xs text-ink-faint">Dr. Ananya Sharma, OBGYN</div>
              <div className="text-sm text-ink-soft mt-1">Plan discharges and set risk flags</div>
            </div>
            <span className="text-sm text-scrub font-semibold shrink-0">
              {loadingRole === 'Doctor' ? 'Signing in…' : 'Sign in'}
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleOneClickLogin('Coordinator')}
            disabled={!!loadingRole}
            className="w-full px-5 py-4 border-t border-rule text-left flex items-center justify-between gap-4 hover:bg-paper cursor-pointer disabled:cursor-default"
          >
            <div>
              <div className="text-sm font-semibold text-ink">Nurse coordinator</div>
              <div className="text-xs text-ink-faint">Priya Patel</div>
              <div className="text-sm text-ink-soft mt-1">Call mothers who are due or late</div>
            </div>
            <span className="text-sm text-scrub font-semibold shrink-0">
              {loadingRole === 'Coordinator' ? 'Signing in…' : 'Sign in'}
            </span>
          </button>

          <button
            type="button"
            onClick={() => handleOneClickLogin('Admin')}
            disabled={!!loadingRole}
            className="w-full px-5 py-4 border-t border-rule text-left flex items-center justify-between gap-4 hover:bg-paper cursor-pointer disabled:cursor-default rounded-b-md"
          >
            <div>
              <div className="text-sm font-semibold text-ink">Hospital admin</div>
              <div className="text-xs text-ink-faint">Rajesh Kumar</div>
              <div className="text-sm text-ink-soft mt-1">See outcomes and manage staff</div>
            </div>
            <span className="text-sm text-scrub font-semibold shrink-0">
              {loadingRole === 'Admin' ? 'Signing in…' : 'Sign in'}
            </span>
          </button>
        </div>

        <p className="text-xs text-ink-faint mt-8">
          Photo: Dream_ maKkerzz on{' '}
          <a
            href="https://www.pexels.com/photo/joyful-indian-family-with-newborn-baby-portrait-30012200/"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            Pexels
          </a>
        </p>
        </div>
      </div>
    </div>
  );
}
