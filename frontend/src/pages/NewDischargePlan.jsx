import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { errorMessage, patientApi } from '../api/client';
import { ErrorBanner, PageShell } from '../components/Feedback';
import FOGSIRiskCalculator from '../components/FOGSIRiskCalculator';
import { useToast } from '../components/Toast';
import { formatDate, todayISO } from '../lib/format';
import { LANGUAGES, REMINDER_LANGUAGES, RISK_TIERS, visitLabel } from '../lib/labels';
import { flagsFor } from '../lib/risk';

const TIER_SUMMARY = {
  standard: 'She gets the four WHO checkups.',
  moderate: 'Extra checks at 2 and 4 weeks, on top of the four WHO checkups.',
  high: 'A check every week for the first 4 weeks, on top of the four WHO checkups.',
  specialist: 'A specialist follow-up at 2 weeks, on top of the four WHO checkups.',
};

export default function NewDischargePlan() {
  const navigate = useNavigate();
  const toast = useToast();
  const today = todayISO();

  const [form, setForm] = useState({
    name: '',
    contact_number: '',
    preferred_language: 'Hindi',
    delivery_date: today,
    discharge_date: today,
    newborn_gender: 'Female',
    newborn_name: '',
  });
  const [criteria, setCriteria] = useState([]);
  const [preview, setPreview] = useState(null);
  const [previewError, setPreviewError] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const riskFlags = useMemo(() => flagsFor(criteria), [criteria]);
  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  useEffect(() => {
    if (!form.delivery_date) return undefined;
    let cancelled = false;
    const timer = setTimeout(() => {
      patientApi
        .previewSchedule(form.delivery_date, riskFlags)
        .then((res) => {
          if (!cancelled) {
            setPreview(res.data);
            setPreviewError('');
          }
        })
        .catch((err) => !cancelled && setPreviewError(errorMessage(err, "Couldn't load the schedule preview.")));
    }, 150);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [form.delivery_date, riskFlags]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (form.discharge_date < form.delivery_date) {
      setError("The discharge date can't be before the delivery date.");
      return;
    }
    setSaving(true);
    try {
      const res = await patientApi.createPatient({ ...form, risk_flags: riskFlags });
      const { patient, active_plan } = res.data;
      toast.success(`${patient.name} is discharged with ${active_plan.visits.length} checkups scheduled.`);
      navigate(`/patients/${patient.patient_id}`);
    } catch (err) {
      setError(errorMessage(err, "Couldn't create the discharge plan. Check the details and try again."));
      setSaving(false);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    }
  };

  const tier = preview
    ? { ...RISK_TIERS[preview.risk_tier], summary: TIER_SUMMARY[preview.risk_tier] }
    : null;

  return (
    <PageShell>
      <h1 className="text-2xl font-bold">New discharge</h1>
      <p className="text-sm text-ink-soft mt-1">
        Add the mother and baby. Cara schedules her checkups from the delivery date.
      </p>

      {error && (
        <div className="mt-6">
          <ErrorBanner message={error} />
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 max-w-2xl">
          <fieldset>
            <legend className="text-base font-bold mb-4">Mother</legend>
            <div className="space-y-4">
              <div>
                <label htmlFor="mother-name" className="label">
                  Full name
                </label>
                <input id="mother-name" type="text" required minLength={2} value={form.name} onChange={set('name')} className="field" />
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="mother-phone" className="label">
                    Mobile number
                  </label>
                  <input
                    id="mother-phone"
                    type="tel"
                    inputMode="tel"
                    required
                    value={form.contact_number}
                    onChange={set('contact_number')}
                    placeholder="98765 43210"
                    className="field"
                  />
                  <p className="hint">WhatsApp first, SMS if that fails. +91 is added for 10-digit numbers.</p>
                </div>
                <div>
                  <label htmlFor="mother-language" className="label">
                    Language
                  </label>
                  <select id="mother-language" value={form.preferred_language} onChange={set('preferred_language')} className="field">
                    {LANGUAGES.map((l) => (
                      <option key={l} value={l}>
                        {l}
                      </option>
                    ))}
                  </select>
                  <p className="hint">
                    {REMINDER_LANGUAGES.includes(form.preferred_language)
                      ? `Reminders are sent in ${form.preferred_language}.`
                      : `No reviewed ${form.preferred_language} template yet; reminders go in English.`}
                  </p>
                </div>
              </div>
            </div>
          </fieldset>

          <fieldset className="border-t border-rule pt-6 mt-8">
            <legend className="text-base font-bold mb-4 float-left w-full">Baby</legend>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 clear-both">
              <div>
                <label htmlFor="baby-name" className="label">
                  Name <span className="font-normal text-ink-faint">(optional)</span>
                </label>
                <input id="baby-name" type="text" value={form.newborn_name} onChange={set('newborn_name')} className="field" />
                <p className="hint">Leave blank if not named yet.</p>
              </div>
              <div>
                <label htmlFor="baby-sex" className="label">
                  Sex
                </label>
                <select id="baby-sex" value={form.newborn_gender} onChange={set('newborn_gender')} className="field">
                  <option value="Female">Female</option>
                  <option value="Male">Male</option>
                </select>
              </div>
            </div>
          </fieldset>

          <fieldset className="border-t border-rule pt-6 mt-8">
            <legend className="text-base font-bold mb-4 float-left w-full">Dates</legend>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 clear-both">
              <div>
                <label htmlFor="delivery-date" className="label">
                  Delivery date
                </label>
                <input
                  id="delivery-date"
                  type="date"
                  required
                  max={today}
                  value={form.delivery_date}
                  onChange={set('delivery_date')}
                  className="field"
                />
              </div>
              <div>
                <label htmlFor="discharge-date" className="label">
                  Discharge date
                </label>
                <input
                  id="discharge-date"
                  type="date"
                  required
                  min={form.delivery_date}
                  max={today}
                  value={form.discharge_date}
                  onChange={set('discharge_date')}
                  className="field"
                />
              </div>
            </div>
          </fieldset>

          <section className="border-t border-rule pt-6 mt-8">
            <h2 className="text-base font-bold">Checkups Cara will schedule</h2>
            {previewError && (
              <div className="mt-4">
                <ErrorBanner message={previewError} />
              </div>
            )}
            {preview && (
              <div className="mt-4 card">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-rule">
                      <th className="th py-2">Checkup</th>
                      <th className="th py-2">Due</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.visits.map((v) => (
                      <tr key={`${v.visit_type}-${v.due_date}`} className="border-b border-rule last:border-0">
                        <td className="py-3 px-4 text-sm">
                          {visitLabel(v.visit_type)}
                          {v.is_risk_visit && <span className="ml-2 text-xs font-semibold text-late">extra</span>}
                        </td>
                        <td className="py-3 px-4 text-sm text-ink-soft">{formatDate(v.due_date)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <div className="border-t border-rule pt-6 mt-8 flex justify-end gap-3">
            <button type="button" onClick={() => navigate('/worklist')} className="btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? 'Creating…' : 'Create discharge plan'}
            </button>
          </div>
        </div>

        <div className="border-t border-rule pt-6 lg:border-0 lg:pt-0">
          <h2 className="text-base font-bold mb-4">Risk</h2>
          <FOGSIRiskCalculator selected={criteria} onChange={setCriteria} tier={tier} />
        </div>
      </form>
    </PageShell>
  );
}
