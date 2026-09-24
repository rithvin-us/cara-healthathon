import React, { useState, useEffect } from 'react';
import { adminApi } from '../api/client';

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
      alert("Couldn't change access: " + (err.response?.data?.detail || err.message));
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
      setFormError(err.response?.data?.detail || "Couldn't add this person. Check the details and try again.");
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-sm text-ink-soft">Loading…</p>
      </div>
    );
  }

  const inputClass =
    'mt-1 block w-full text-sm border border-rule-strong rounded px-3 py-2 bg-white focus:outline-none focus:border-scrub focus:ring-1 focus:ring-scrub';

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="md:flex md:items-start md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink">Staff</h1>
          <p className="text-sm text-ink-soft mt-1">People who can sign in to Cara at this hospital.</p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="mt-4 md:mt-0 bg-scrub hover:bg-scrub-dark text-white text-sm font-semibold px-4 py-2 rounded"
        >
          Add a staff member
        </button>
      </div>

      <div className="bg-white border border-rule rounded-md mt-6 overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="text-left text-[13px] font-semibold text-ink-soft border-b border-rule">
              <th className="py-3 px-4">Name</th>
              <th className="py-3 px-4">Role</th>
              <th className="py-3 px-4">Email</th>
              <th className="py-3 px-4">Access</th>
              <th className="py-3 px-4"><span className="sr-only">Change access</span></th>
            </tr>
          </thead>
          <tbody>
            {staffList.map((user) => (
              <tr key={user.user_id} className="border-b border-rule last:border-0 hover:bg-paper">
                <td className="py-3 px-4 text-sm font-semibold text-ink">{user.name}</td>
                <td className="py-3 px-4 text-sm text-ink">{user.role}</td>
                <td className="py-3 px-4 text-sm text-ink-soft">{user.email}</td>
                <td className="py-3 px-4 text-sm">
                  {user.is_active ? (
                    <span className="text-ok font-semibold">Active</span>
                  ) : (
                    <span className="text-ink-faint">Turned off</span>
                  )}
                </td>
                <td className="py-3 px-4 text-sm text-right">
                  <button
                    onClick={() => handleToggleActive(user.user_id)}
                    className="text-scrub text-sm font-semibold hover:underline underline-offset-2"
                  >
                    {user.is_active ? 'Turn off access' : 'Turn on access'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {digest && (
        <section className="border-t border-rule pt-6 mt-8">
          <h2 className="text-base font-bold text-ink">This week at {digest.facility_name}</h2>
          <p className="text-sm text-ink mt-2 max-w-3xl">{digest.digest_text}</p>
          <p className="text-[13px] text-ink-soft mt-2">
            <span className="text-late font-semibold">{digest.overdue_count} overdue</span>, <span className="text-soon font-semibold">{digest.due_today_count} due today</span>
          </p>
        </section>
      )}

      {showAddModal && (
        <div className="fixed inset-0 bg-ink/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-md shadow-lg max-w-md w-full p-6">
            <h2 className="text-base font-bold text-ink">Add a staff member</h2>
            <p className="text-[13px] text-ink-soft mt-1">They can sign in straight away with this email and password.</p>
            {formError && (
              <div className="border-l-4 border-late bg-late-tint text-late text-sm px-3 py-2 mt-4">{formError}</div>
            )}

            <form onSubmit={handleCreateStaffSubmit} className="space-y-4 mt-4">
              <div>
                <label className="block text-sm font-semibold text-ink">Full name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Dr. Sangeeta Joshi"
                  className={inputClass}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-ink">Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                  className={inputClass}
                >
                  <option value="Doctor">Doctor (OBGYN)</option>
                  <option value="Coordinator">Coordinator (nurse or counsellor)</option>
                  <option value="Admin">Hospital admin</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-ink">Email</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="doctor.joshi@cara.health"
                  className={inputClass}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-ink">Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={inputClass}
                />
                <p className="text-xs text-ink-faint mt-1">Share this with them in person, not over WhatsApp.</p>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="bg-white border border-rule-strong text-ink text-sm font-semibold px-4 py-2 rounded hover:bg-paper"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-scrub hover:bg-scrub-dark text-white text-sm font-semibold px-4 py-2 rounded"
                >
                  Add staff member
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
