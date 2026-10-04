import { useCallback, useEffect, useState } from 'react';
import { adminApi, errorMessage } from '../api/client';
import { ErrorBanner, Loading, PageShell } from '../components/Feedback';
import Modal from '../components/Modal';
import { useToast } from '../components/Toast';
import { useApp } from '../context/AppContext';

const ROLES = [
  { value: 'Doctor', label: 'Doctor (OBGYN)' },
  { value: 'Coordinator', label: 'Coordinator (nurse or counsellor)' },
  { value: 'Admin', label: 'Hospital admin' },
];

function AddStaffModal({ onClose, onSaved }) {
  const [form, setForm] = useState({ name: '', role: 'Coordinator', email: '', password: '' });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await adminApi.createStaff(form);
      onSaved(form.name);
    } catch (err) {
      setError(errorMessage(err, "Couldn't add this person."));
      setSaving(false);
    }
  };

  return (
    <Modal title="Add a staff member" subtitle="They can sign in straight away with this email and password." onClose={onClose}>
      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="s-name" className="label">
            Full name
          </label>
          <input id="s-name" required minLength={2} value={form.name} onChange={set('name')} placeholder="Dr. Sangeeta Joshi" className="field" />
        </div>
        <div>
          <label htmlFor="s-role" className="label">
            Role
          </label>
          <select id="s-role" value={form.role} onChange={set('role')} className="field">
            {ROLES.map((r) => (
              <option key={r.value} value={r.value}>
                {r.label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="s-email" className="label">
            Email
          </label>
          <input id="s-email" type="email" required value={form.email} onChange={set('email')} autoComplete="off" className="field" />
        </div>
        <div>
          <label htmlFor="s-password" className="label">
            Password
          </label>
          <input
            id="s-password"
            type="password"
            required
            minLength={8}
            value={form.password}
            onChange={set('password')}
            autoComplete="new-password"
            className="field"
          />
          <p className="hint">At least 8 characters. Share it in person, not over WhatsApp.</p>
        </div>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Adding…' : 'Add staff member'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function StaffAdmin() {
  const { user, health, refreshData } = useApp();
  const toast = useToast();
  const [staff, setStaff] = useState([]);
  const [digest, setDigest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [adding, setAdding] = useState(false);
  const [confirmReset, setConfirmReset] = useState(false);
  const [busy, setBusy] = useState(null);

  const load = useCallback(async () => {
    setError('');
    try {
      const [staffRes, digestRes] = await Promise.all([adminApi.getStaff(), adminApi.getWeeklyDigest()]);
      setStaff(staffRes.data);
      setDigest(digestRes.data);
    } catch (err) {
      setError(errorMessage(err, "Couldn't load staff."));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const toggle = async (member) => {
    setBusy(member.user_id);
    try {
      await adminApi.toggleStaffActive(member.user_id);
      toast.success(`${member.name}'s access is ${member.is_active ? 'turned off' : 'turned on'}.`);
      load();
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't change access."));
    } finally {
      setBusy(null);
    }
  };

  const resetDemo = async () => {
    setBusy('reset');
    try {
      const { data } = await adminApi.resetDemo();
      toast.success(`Demo data reset: ${data.patients} mothers, ${data.visits} visits.`);
      setConfirmReset(false);
      refreshData();
      load();
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't reset the demo data."));
    } finally {
      setBusy(null);
    }
  };

  if (loading) {
    return (
      <PageShell>
        <Loading />
      </PageShell>
    );
  }

  return (
    <PageShell>
      <div className="md:flex md:items-start md:justify-between">
        <div>
          <h1 className="text-2xl font-bold">Staff</h1>
          <p className="text-sm text-ink-soft mt-1">People who can sign in to Cara at {user.facility_name}.</p>
        </div>
        <button type="button" onClick={() => setAdding(true)} className="btn-primary mt-4 md:mt-0">
          Add a staff member
        </button>
      </div>

      {error && (
        <div className="mt-6">
          <ErrorBanner message={error} onRetry={load} />
        </div>
      )}

      <div className="card mt-6 overflow-x-auto">
        <table className="min-w-full">
          <thead>
            <tr className="border-b border-rule">
              <th className="th">Name</th>
              <th className="th">Role</th>
              <th className="th">Email</th>
              <th className="th">Access</th>
              <th className="th">
                <span className="sr-only">Change access</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {staff.map((member) => (
              <tr key={member.user_id} className="border-b border-rule last:border-0 hover:bg-paper">
                <td className="py-3 px-4 text-sm font-semibold">
                  {member.name}
                  {member.user_id === user.user_id && <span className="font-normal text-ink-faint"> (you)</span>}
                </td>
                <td className="py-3 px-4 text-sm">{member.role}</td>
                <td className="py-3 px-4 text-sm text-ink-soft">{member.email}</td>
                <td className="py-3 px-4 text-sm">
                  {member.is_active ? (
                    <span className="text-ok font-semibold">Active</span>
                  ) : (
                    <span className="text-ink-faint">Turned off</span>
                  )}
                </td>
                <td className="py-3 px-4 text-sm text-right">
                  {member.user_id !== user.user_id && (
                    <button
                      type="button"
                      onClick={() => toggle(member)}
                      disabled={busy === member.user_id}
                      className={member.is_active ? 'btn-danger-link' : 'btn-link'}
                    >
                      {member.is_active ? 'Turn off access' : 'Turn on access'}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {digest && (
        <section className="border-t border-rule pt-6 mt-8">
          <h2 className="text-base font-bold">This week</h2>
          <p className="text-sm mt-2 max-w-3xl">{digest.digest_text}</p>
          <p className="text-[13px] text-ink-soft mt-2">
            <span className="text-late font-semibold">{digest.overdue_count} overdue</span>,{' '}
            <span className="text-soon font-semibold">{digest.due_today_count} due today</span>
          </p>
        </section>
      )}

      {health?.demo_mode && (
        <section className="border-t border-rule pt-6 mt-8">
          <h2 className="text-base font-bold">Demo data</h2>
          <p className="text-sm text-ink-soft mt-2 max-w-2xl">
            Put every synthetic mother, visit and reminder back to the starting state, for example before recording a
            walkthrough. Only available in demo mode.
          </p>
          <button type="button" onClick={() => setConfirmReset(true)} className="btn-secondary mt-3">
            Reset demo data
          </button>
        </section>
      )}

      {adding && (
        <AddStaffModal
          onClose={() => setAdding(false)}
          onSaved={(name) => {
            toast.success(`${name} can now sign in.`);
            setAdding(false);
            load();
          }}
        />
      )}

      {confirmReset && (
        <Modal
          title="Reset demo data?"
          subtitle="Every change made since the last reset is lost, including staff you added."
          onClose={() => setConfirmReset(false)}
          size="sm"
        >
          <div className="flex justify-end gap-3">
            <button type="button" onClick={() => setConfirmReset(false)} className="btn-secondary">
              Cancel
            </button>
            <button type="button" onClick={resetDemo} className="btn-primary" disabled={busy === 'reset'}>
              {busy === 'reset' ? 'Resetting…' : 'Reset'}
            </button>
          </div>
        </Modal>
      )}
    </PageShell>
  );
}
