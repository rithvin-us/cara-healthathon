import React, { useState, useEffect } from 'react';
import { adminApi } from '../api/client';
import { Shield, UserPlus, UserCheck, UserX, FileText, CheckCircle, AlertCircle } from 'lucide-react';

export default function StaffAdmin() {
  const [staffList, setStaffList] = useState([]);
  const [digest, setDigest] = useState(null);
  const [loading, setLoading] = useState(true);

  // New staff form
  const [name, setName] = useState('');
  const [role, setRole] = useState('Doctor');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  const loadData = async () => {
    setLoading(true);
    try {
      const [staffRes, digestRes] = await Promise.all([
        adminApi.getStaff(),
        adminApi.getWeeklyDigest(),
      ]);
      setStaffList(staffRes.data);
      setDigest(digestRes.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleToggleActive = async (userId) => {
    try {
      await adminApi.toggleStaffActive(userId);
      loadData();
    } catch (err) {
      alert('Error toggling staff status: ' + (err.response?.data?.detail || err.message));
    }
  };

  const handleCreateStaffSubmit = async (e) => {
    e.preventDefault();
    setFormError('');
    try {
      await adminApi.createStaff({
        name,
        role,
        email,
        password,
        facility_id: 1,
      });
      setShowAddModal(false);
      setName('');
      setEmail('');
      setPassword('');
      loadData();
    } catch (err) {
      setFormError(err.response?.data?.detail || 'Failed to create staff account.');
    }
  };

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-600 border-t-transparent"></div>
        <p className="mt-2 text-sm text-slate-500">Loading admin portal...</p>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Facility Staff Administration</h1>
          <p className="text-sm text-slate-600">
            FR-022: Manage facility staff user accounts and review AI plain-language weekly summary digests (FR-012).
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="mt-4 md:mt-0 flex items-center space-x-1.5 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-sm font-semibold shadow-sm transition"
        >
          <UserPlus className="h-4 w-4" />
          <span>Add Staff Account</span>
        </button>
      </div>

      {/* Weekly Digest Section (FR-012) */}
      {digest && (
        <div className="bg-emerald-900 text-white p-6 rounded-xl shadow-md space-y-2">
          <div className="flex items-center space-x-2 text-emerald-200 text-xs font-bold uppercase tracking-wider">
            <FileText className="h-4 w-4 text-emerald-400" />
            <span>Weekly Plain-Language Coordinator Digest (FR-012)</span>
          </div>
          <p className="text-sm font-medium leading-relaxed bg-emerald-950/60 p-4 rounded-lg border border-emerald-700/50">
            "{digest.digest_text}"
          </p>
          <div className="text-[11px] text-emerald-300 flex items-center justify-between pt-1">
            <span>Facility: {digest.facility_name}</span>
            <span>Overdue Visits: {digest.overdue_count} | Due Today: {digest.due_today_count}</span>
          </div>
        </div>
      )}

      {/* Staff User Accounts Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-4 p-6">
        <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3 flex items-center space-x-2">
          <Shield className="h-5 w-5 text-emerald-700" />
          <span>Registered Staff User Accounts ({staffList.length})</span>
        </h3>

        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-bold text-slate-600 uppercase">Staff Member</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-slate-600 uppercase">Assigned Role</th>
              <th className="px-6 py-3 text-left text-xs font-bold text-slate-600 uppercase">Email</th>
              <th className="px-6 py-3 text-center text-xs font-bold text-slate-600 uppercase">Status</th>
              <th className="px-6 py-3 text-right text-xs font-bold text-slate-600 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {staffList.map((user) => (
              <tr key={user.user_id} className="hover:bg-slate-50 transition">
                <td className="px-6 py-4 font-bold text-slate-900">{user.name}</td>
                <td className="px-6 py-4">
                  <span className="px-2.5 py-1 rounded text-xs font-semibold bg-emerald-100 text-emerald-800">
                    {user.role}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-600 font-mono text-xs">{user.email}</td>
                <td className="px-6 py-4 text-center">
                  {user.is_active ? (
                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-100 text-emerald-800">Active</span>
                  ) : (
                    <span className="px-2 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-500">Deactivated</span>
                  )}
                </td>
                <td className="px-6 py-4 text-right">
                  <button
                    onClick={() => handleToggleActive(user.user_id)}
                    className={`text-xs font-semibold px-3 py-1.5 rounded transition ${
                      user.is_active
                        ? 'bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200'
                        : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                    }`}
                  >
                    {user.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Add Staff Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-slate-900 bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Onboard Staff Member</h3>
            {formError && <div className="mb-3 text-xs bg-red-50 text-red-700 p-2 rounded">{formError}</div>}

            <form onSubmit={handleCreateStaffSubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700">Full Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Dr. Sangeeta Joshi"
                  className="mt-1 block w-full border border-slate-300 rounded-lg p-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700">Role Assignment</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className="mt-1 block w-full border border-slate-300 rounded-lg p-2 focus:ring-emerald-500 bg-white"
                >
                  <option value="Doctor">Doctor (OBGYN)</option>
                  <option value="Coordinator">Coordinator (Nurse / Counselor)</option>
                  <option value="Admin">Facility Admin</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700">Email Address</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="doctor.joshi@cara.health"
                  className="mt-1 block w-full border border-slate-300 rounded-lg p-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="mt-1 block w-full border border-slate-300 rounded-lg p-2 focus:ring-emerald-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-3 py-1.5 text-xs font-semibold text-slate-600 bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-emerald-700 rounded-lg shadow-sm"
                >
                  Create Staff User
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
