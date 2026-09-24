import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { patientApi, familyApi, visitApi } from '../api/client';
import { User, Phone, Globe, Calendar, Users, ShieldCheck, ShieldOff, Plus, MessageSquare, ArrowLeft, CheckCircle2, AlertCircle, Clock } from 'lucide-react';

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
      alert('Error updating consent: ' + (err.response?.data?.detail || err.message));
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
      setFmError(err.response?.data?.detail || 'Failed to add family member.');
    }
  };

  const handleManualNudge = async (visitId) => {
    try {
      const res = await visitApi.manualNudge(visitId);
      alert(`Nudge re-triggered! Nudge logs created: ${res.data.length}`);
      loadDetail();
    } catch (err) {
      alert('Nudge error: ' + (err.response?.data?.detail || err.message));
    }
  };

  if (loading) {
    return (
      <div className="text-center py-16">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-600 border-t-transparent"></div>
        <p className="mt-2 text-sm text-slate-500">Loading patient details...</p>
      </div>
    );
  }

  if (!data) return <div className="text-center py-12 text-slate-500">Patient record not found.</div>;

  const { patient, active_plan, family_members, nudges } = data;

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* Top Bar */}
      <div>
        <Link to="/worklist" className="inline-flex items-center text-xs font-semibold text-emerald-700 hover:text-emerald-800 mb-2">
          <ArrowLeft className="h-3.5 w-3.5 mr-1" />
          <span>Back to Worklist</span>
        </Link>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{patient.name}</h1>
          <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800">
            Active Patient Record #{patient.patient_id}
          </span>
        </div>
      </div>

      {/* Patient Header Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-4 gap-4 text-sm">
        <div>
          <span className="text-xs text-slate-400 font-semibold block uppercase">Contact Number</span>
          <span className="font-bold text-slate-900 flex items-center space-x-1 mt-0.5">
            <Phone className="h-4 w-4 text-slate-400 mr-1" />
            {patient.contact_number}
          </span>
        </div>

        <div>
          <span className="text-xs text-slate-400 font-semibold block uppercase">Preferred Language</span>
          <span className="font-bold text-slate-900 flex items-center space-x-1 mt-0.5">
            <Globe className="h-4 w-4 text-slate-400 mr-1" />
            {patient.preferred_language}
          </span>
        </div>

        <div>
          <span className="text-xs text-slate-400 font-semibold block uppercase">Delivery Date</span>
          <span className="font-bold text-slate-900 flex items-center space-x-1 mt-0.5">
            <Calendar className="h-4 w-4 text-slate-400 mr-1" />
            {patient.delivery_date}
          </span>
        </div>

        <div>
          <span className="text-xs text-slate-400 font-semibold block uppercase">Discharge Date</span>
          <span className="font-bold text-slate-900 flex items-center space-x-1 mt-0.5">
            <Calendar className="h-4 w-4 text-slate-400 mr-1" />
            {patient.discharge_date}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Visit Schedule Timeline (2 Cols) */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3 flex items-center justify-between">
            <span>Postnatal Visit Calendar</span>
            {active_plan && active_plan.risk_flags.length > 0 && (
              <span className="text-xs font-semibold px-2.5 py-0.5 bg-rose-100 text-rose-800 rounded">
                Risk Override Applied
              </span>
            )}
          </h3>

          {!active_plan || active_plan.visits.length === 0 ? (
            <p className="text-sm text-slate-500">No scheduled visits on file.</p>
          ) : (
            <div className="space-y-3">
              {active_plan.visits.map((v) => {
                let statusBadge = null;
                if (v.status === 'completed') {
                  statusBadge = <span className="px-2 py-0.5 rounded text-xs font-bold bg-emerald-100 text-emerald-800">Completed</span>;
                } else if (v.status === 'overdue') {
                  statusBadge = <span className="px-2 py-0.5 rounded text-xs font-bold bg-red-100 text-red-800">Overdue</span>;
                } else if (v.status === 'due_today') {
                  statusBadge = <span className="px-2 py-0.5 rounded text-xs font-bold bg-amber-100 text-amber-800">Due Today</span>;
                } else {
                  statusBadge = <span className="px-2 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-600">Upcoming</span>;
                }

                return (
                  <div key={v.visit_id} className="p-4 rounded-lg border border-slate-200 bg-slate-50 flex items-center justify-between">
                    <div>
                      <div className="font-bold text-slate-900 text-sm flex items-center space-x-2">
                        <span>{v.visit_type}</span>
                        {statusBadge}
                      </div>
                      <div className="text-xs text-slate-500 mt-1">Due Date: {v.due_date}</div>
                      {v.note && <div className="text-xs text-slate-600 mt-1 italic">Note: "{v.note}"</div>}
                    </div>

                    <button
                      onClick={() => handleManualNudge(v.visit_id)}
                      className="px-3 py-1 text-xs font-semibold text-emerald-800 bg-emerald-100 hover:bg-emerald-200 rounded-lg transition"
                    >
                      Nudge
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Family Consent & Access Manager (1 Col) */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-base font-bold text-slate-900 flex items-center space-x-1.5">
              <Users className="h-5 w-5 text-emerald-700" />
              <span>Family Access (FR-016/017)</span>
            </h3>
            <button
              onClick={() => setShowAddFamily(true)}
              className="p-1 rounded bg-emerald-50 text-emerald-700 hover:bg-emerald-100 transition"
              title="Add Consented Family Member"
            >
              <Plus className="h-4 w-4" />
            </button>
          </div>

          {family_members.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No secondary family member added yet.</p>
          ) : (
            <div className="space-y-3">
              {family_members.map((fm) => (
                <div key={fm.family_id} className="p-3 rounded-lg border border-slate-200 bg-slate-50 space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="font-semibold text-sm text-slate-900">{fm.name} ({fm.relation})</div>
                    {fm.latest_consent ? (
                      <span className="flex items-center text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded">
                        <ShieldCheck className="h-3 w-3 mr-1" />
                        Consent Active
                      </span>
                    ) : (
                      <span className="flex items-center text-[10px] font-bold text-rose-700 bg-rose-100 px-2 py-0.5 rounded">
                        <ShieldOff className="h-3 w-3 mr-1" />
                        Revoked
                      </span>
                    )}
                  </div>
                  <div className="text-xs text-slate-500">{fm.contact_number}</div>

                  <button
                    onClick={() => handleToggleConsent(fm.family_id, fm.latest_consent)}
                    className={`w-full text-xs font-semibold py-1 rounded transition ${
                      fm.latest_consent
                        ? 'bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200'
                        : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                    }`}
                  >
                    {fm.latest_consent ? 'Revoke Consent' : 'Grant Consent'}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Add Family Member Modal */}
      {showAddFamily && (
        <div className="fixed inset-0 bg-slate-900 bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-4">Add Consented Family Member</h3>
            {fmError && <div className="mb-3 text-xs bg-red-50 text-red-700 p-2 rounded">{fmError}</div>}

            <form onSubmit={handleAddFamilySubmit} className="space-y-4 text-sm">
              <div>
                <label className="block text-xs font-semibold text-slate-700">Full Name</label>
                <input
                  type="text"
                  required
                  value={fmName}
                  onChange={(e) => setFmName(e.target.value)}
                  placeholder="e.g. Ramesh Rao"
                  className="mt-1 block w-full border border-slate-300 rounded-lg p-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700">Relation to Mother</label>
                <select
                  value={fmRelation}
                  onChange={(e) => setFmRelation(e.target.value)}
                  className="mt-1 block w-full border border-slate-300 rounded-lg p-2 focus:ring-emerald-500 focus:border-emerald-500 bg-white"
                >
                  <option value="Husband">Husband</option>
                  <option value="Mother">Mother</option>
                  <option value="Sister">Sister</option>
                  <option value="Mother-in-law">Mother-in-law</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700">Contact Number</label>
                <input
                  type="text"
                  required
                  value={fmContact}
                  onChange={(e) => setFmContact(e.target.value)}
                  placeholder="+919876543211"
                  className="mt-1 block w-full border border-slate-300 rounded-lg p-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="consent_check"
                  checked={fmConsent}
                  onChange={(e) => setFmConsent(e.target.checked)}
                  className="h-4 w-4 text-emerald-600 rounded"
                />
                <label htmlFor="consent_check" className="text-xs font-medium text-slate-700">
                  Verbal/Written Consent Captured (Opt-in for WhatsApp nudges)
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddFamily(false)}
                  className="px-3 py-1.5 text-xs font-semibold text-slate-600 bg-slate-100 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-semibold text-white bg-emerald-700 rounded-lg shadow-sm"
                >
                  Save Contact
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
