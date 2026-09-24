import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { patientApi, familyApi, visitApi } from '../api/client';
import { ArrowLeft } from 'lucide-react';
import { visitLabel } from '../labels';

export default function PatientDetail() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Add Family Modal
  const [showAddFamily, setShowAddFamily] = useState(false);
  const [fmName, setFmName] = useState('');
  const [fmRelation, setFmRelation] = useState('Husband');
  const [fmContact, setFmContact] = useState('');
  const [fmConsent, setFmConsent] = useState(true);
  const [fmError, setFmError] = useState('');

  const loadDetail = async () => {
    setLoading(true);
    try {
      const res = await patientApi.getPatientDetail(id);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDetail();
  }, [id]);

  const handleToggleConsent = async (familyId, currentConsent) => {
    try {
      await familyApi.updateConsent(familyId, !currentConsent);
      loadDetail();
    } catch (err) {
      alert("Couldn't update consent: " + (err.response?.data?.detail || err.message));
    }
  };

  const handleAddFamilySubmit = async (e) => {
    e.preventDefault();
    setFmError('');
    try {
      await familyApi.addFamilyMember(id, {
        name: fmName,
        relation: fmRelation,
        contact_number: fmContact,
        preferred_language: data.patient.preferred_language,
        consent_given: fmConsent,
      });
      setShowAddFamily(false);
      setFmName('');
      setFmContact('');
      loadDetail();
    } catch (err) {
      setFmError(err.response?.data?.detail || "Couldn't add this family member. Check the details and try again.");
    }
  };

  const handleManualNudge = async (visitId) => {
    try {
      const res = await visitApi.manualNudge(visitId);
      alert(`Reminder sent to ${res.data.length} ${res.data.length === 1 ? 'number' : 'numbers'}.`);
      loadDetail();
    } catch (err) {
      alert("Couldn't send reminder: " + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-sm text-ink-soft">Loading…</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="text-sm text-ink-soft">We couldn't find this mother's record. Go back to the follow-up list and open her again.</p>
      </div>
    );
  }

  const { patient, active_plan, family_members, nudges } = data;

  const riskNames = {
    hypertension: 'High blood pressure',
    hemorrhage_history: 'History of heavy bleeding (PPH)',
    anemia: 'Severe anaemia',
    c_section: 'C-section',
    other: 'Other risk',
  };

  const inputClass =
    'mt-1 block w-full text-sm border border-rule-strong rounded px-3 py-2 bg-white focus:outline-none focus:border-scrub focus:ring-1 focus:ring-scrub';

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <Link
        to="/worklist"
        className="inline-flex items-center text-scrub text-sm font-semibold hover:underline underline-offset-2 mb-4"
      >
        <ArrowLeft className="h-4 w-4 mr-1" />
        <span>Back to follow-ups</span>
      </Link>

      <h1 className="text-2xl font-bold text-ink">{patient.name}</h1>
      <p className="text-sm text-ink-soft mt-1">
        Delivered on {patient.delivery_date}, discharged on {patient.discharge_date}. Speaks {patient.preferred_language}. Phone {patient.contact_number}.
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-10">
        <div className="lg:col-span-2">
          <section className="border-t border-rule pt-6 mt-8">
            <h2 className="text-base font-bold text-ink">Checkup schedule</h2>

            {!active_plan || active_plan.visits.length === 0 ? (
              <p className="text-sm text-ink-soft mt-3">No checkups are scheduled. Create a discharge plan to set up her visits.</p>
            ) : (
              <ol className="mt-4 border-l-2 border-rule">
                {[...active_plan.visits]
                  .sort((a, b) => String(a.due_date).localeCompare(String(b.due_date)))
                  .map((v) => {
                    let status;
                    if (v.status === 'completed') {
                      status = <span className="text-ok font-semibold">Visited</span>;
                    } else if (v.status === 'overdue') {
                      status = <span className="text-late font-semibold">Late</span>;
                    } else if (v.status === 'due_today') {
                      status = <span className="text-soon font-semibold">Due today</span>;
                    } else {
                      status = <span className="text-ink-soft">Upcoming</span>;
                    }

                    return (
                      <li key={v.visit_id} className="relative pl-5 py-3 border-b border-rule last:border-0">
                        <span className="absolute -left-[5px] top-5 h-2 w-2 bg-rule-strong" aria-hidden="true"></span>
                        <div className="flex items-start justify-between gap-4">
                          <div className="text-sm">
                            <div className="font-semibold text-ink">{visitLabel(v.visit_type)}</div>
                            <div className="text-[13px] text-ink-soft mt-0.5">
                              Due {v.due_date}. {status}
                            </div>
                            {v.note && <div className="text-[13px] text-ink-soft mt-1">Note: {v.note}</div>}
                          </div>

                          <button
                            onClick={() => handleManualNudge(v.visit_id)}
                            className="shrink-0 text-scrub text-sm font-semibold hover:underline underline-offset-2"
                          >
                            Send reminder
                          </button>
                        </div>
                      </li>
                    );
                  })}
              </ol>
            )}
          </section>
        </div>

        <div>
          <section className="border-t border-rule pt-6 mt-8">
            <h2 className="text-base font-bold text-ink">Risk flags</h2>
            {active_plan && active_plan.risk_flags.length > 0 ? (
              <>
                <p className="text-sm text-late font-semibold mt-3">
                  {active_plan.risk_flags.map((rf) => riskNames[rf.flag_type] || rf.flag_type).join(', ')}
                </p>
                <p className="text-xs text-ink-faint mt-1">Extra checkups have been added to her schedule for these.</p>
              </>
            ) : (
              <p className="text-sm text-ink-soft mt-3">None recorded. She follows the standard PNC schedule.</p>
            )}
          </section>

          <section className="border-t border-rule pt-6 mt-8">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-ink">Family contacts</h2>
              <button
                onClick={() => setShowAddFamily(true)}
                className="text-scrub text-sm font-semibold hover:underline underline-offset-2"
              >
                Add family member
              </button>
            </div>

            {family_members.length === 0 ? (
              <p className="text-sm text-ink-soft mt-3">
                No family members added. Add one if she wants a relative to get her reminders too.
              </p>
            ) : (
              <ul className="mt-3">
                {family_members.map((fm) => (
                  <li key={fm.family_id} className="py-3 border-b border-rule last:border-0 text-sm">
                    <div className="font-semibold text-ink">
                      {fm.name}, {fm.relation.toLowerCase()}
                    </div>
                    <div className="text-[13px] text-ink-soft mt-0.5">{fm.contact_number}</div>
                    <div className="flex items-center justify-between mt-1">
                      {fm.latest_consent ? (
                        <span className="text-[13px] text-ok font-semibold">Agreed to receive reminders</span>
                      ) : (
                        <span className="text-[13px] text-late font-semibold">Consent withdrawn</span>
                      )}
                      <button
                        onClick={() => handleToggleConsent(fm.family_id, fm.latest_consent)}
                        className={`text-sm font-semibold hover:underline underline-offset-2 ${
                          fm.latest_consent ? 'text-late' : 'text-scrub'
                        }`}
                      >
                        {fm.latest_consent ? 'Withdraw consent' : 'Record consent'}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>

      {showAddFamily && (
        <div className="fixed inset-0 bg-ink/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-md shadow-lg max-w-md w-full p-6">
            <h2 className="text-lg font-bold text-ink mb-4">Add family member</h2>
            {fmError && (
              <div className="mb-4 border-l-4 border-late bg-late-tint text-late text-sm px-3 py-2">{fmError}</div>
            )}

            <form onSubmit={handleAddFamilySubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-sm font-semibold text-ink">Name</label>
                <input
                  type="text"
                  required
                  value={fmName}
                  onChange={(e) => setFmName(e.target.value)}
                  placeholder="Ramesh Rao"
                  className={inputClass}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-ink">Relation to mother</label>
                <select
                  value={fmRelation}
                  onChange={(e) => setFmRelation(e.target.value)}
                  className={inputClass}
                >
                  <option value="Husband">Husband</option>
                  <option value="Mother">Mother</option>
                  <option value="Sister">Sister</option>
                  <option value="Mother-in-law">Mother-in-law</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-semibold text-ink">Phone number</label>
                <input
                  type="text"
                  required
                  value={fmContact}
                  onChange={(e) => setFmContact(e.target.value)}
                  placeholder="+919876543211"
                  className={inputClass}
                />
                <p className="text-xs text-ink-faint mt-1">Include the country code, e.g. +91.</p>
              </div>

              <div className="flex items-start gap-2 pt-1">
                <input
                  type="checkbox"
                  id="consent_check"
                  checked={fmConsent}
                  onChange={(e) => setFmConsent(e.target.checked)}
                  className="h-4 w-4 mt-0.5 accent-scrub"
                />
                <label htmlFor="consent_check" className="text-sm text-ink">
                  They agreed, verbally or in writing, to get WhatsApp reminders about her checkups.
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-rule">
                <button
                  type="button"
                  onClick={() => setShowAddFamily(false)}
                  className="bg-white border border-rule-strong text-ink text-sm font-semibold px-4 py-2 rounded hover:bg-paper"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-scrub hover:bg-scrub-dark text-white text-sm font-semibold px-4 py-2 rounded"
                >
                  Add family member
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
