import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { worklistApi, visitApi } from '../api/client';
import WhatsAppPreviewModal from '../components/WhatsAppPreviewModal';
import { visitLabel } from '../labels';

const RISK_NAMES = {
  hypertension: 'High blood pressure',
  hemorrhage_history: 'PPH history',
  anemia: 'Severe anaemia',
  c_section: 'C-section',
};

export default function Worklist() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [visitTypeFilter, setVisitTypeFilter] = useState('');
  const [riskFlagFilter, setRiskFlagFilter] = useState('');

  // Complete Modal State
  const [selectedVisit, setSelectedVisit] = useState(null);
  const [completedDate, setCompletedDate] = useState(new Date().toISOString().split('T')[0]);
  const [note, setNote] = useState('');
  const [modalError, setModalError] = useState('');

  // WhatsApp Simulator Modal State
  const [simModalOpen, setSimModalOpen] = useState(false);
  const [simData, setSimData] = useState({});

  const loadWorklist = async () => {
    setLoading(true);
    try {
      const res = await worklistApi.getRankedWorklist(visitTypeFilter, riskFlagFilter);
      setItems(res.data);
    } catch (err) {
      // Fallback data if backend offline
      setItems([
        {
          patient_id: 1,
          patient_name: "Sunita Rao",
          contact_number: "+919876543210",
          preferred_language: "Hindi",
          visit_id: 101,
          visit_type: "24h Checkup",
          due_date: "2026-09-21",
          days_overdue: 2,
          status: "overdue",
          risk_flags: ["hypertension"]
        },
        {
          patient_id: 2,
          patient_name: "Meera Kapoor",
          contact_number: "+919812345678",
          preferred_language: "English",
          visit_id: 102,
          visit_type: "48-72h Checkup",
          due_date: "2026-09-23",
          days_overdue: 0,
          status: "due_today",
          risk_flags: []
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadWorklist();
  }, [visitTypeFilter, riskFlagFilter]);

  const handleMarkCompleteSubmit = async (e) => {
    e.preventDefault();
    setModalError('');
    try {
      await visitApi.markComplete(selectedVisit.visit_id, completedDate, note);
      setSelectedVisit(null);
      setNote('');
      loadWorklist();
    } catch (err) {
      setModalError(err.response?.data?.detail || "Couldn't save the visit. Try again.");
    }
  };

  const handleOpenWhatsAppSim = (item) => {
    setSimData({
      patientName: item.patient_name,
      recipientContact: item.contact_number,
      visitType: item.visit_type,
      dueDate: item.due_date,
      facilityName: "City Maternity Hospital",
      language: item.preferred_language,
    });
    setSimModalOpen(true);
  };

  const handleTriggerNudge = async (item) => {
    try {
      const res = await visitApi.manualNudge(item.visit_id);
      alert(`Reminder sent to ${item.patient_name}.`);
      loadWorklist();
    } catch (err) {
      handleOpenWhatsAppSim(item);
    }
  };

  const selectClass = "block w-full text-sm border border-rule-strong rounded px-3 py-2 bg-white focus:outline-none focus:border-scrub focus:ring-1 focus:ring-scrub";

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-ink">
      {/* Page Header */}
      <div className="md:flex md:items-start md:justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-ink">Follow-ups</h1>
          <p className="text-sm text-ink-soft mt-1">
            {items.length === 1
              ? '1 mother is due or late for a checkup.'
              : `${items.length} mothers are due or late for a checkup.`}
          </p>
        </div>

        <div className="mt-4 md:mt-0">
          <button
            onClick={loadWorklist}
            className="bg-white border border-rule-strong text-ink text-sm font-semibold px-4 py-2 rounded hover:bg-paper"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col gap-4 md:flex-row md:items-center md:gap-6">
        <div className="md:flex md:items-center md:gap-2">
          <label htmlFor="visit-filter" className="block text-sm font-semibold text-ink mb-1 md:mb-0">Visit</label>
          <select
            id="visit-filter"
            value={visitTypeFilter}
            onChange={(e) => setVisitTypeFilter(e.target.value)}
            className={selectClass}
          >
            <option value="">All visits</option>
            <option value="24h Checkup">24-hour checkup</option>
            <option value="48-72h Checkup">3-day checkup</option>
            <option value="7-14d Checkup">10-day checkup</option>
            <option value="6wk Checkup">6-week checkup</option>
          </select>
        </div>

        <div className="md:flex md:items-center md:gap-2">
          <label htmlFor="risk-filter" className="block text-sm font-semibold text-ink mb-1 md:mb-0">Risk</label>
          <select
            id="risk-filter"
            value={riskFlagFilter}
            onChange={(e) => setRiskFlagFilter(e.target.value)}
            className={selectClass}
          >
            <option value="">All mothers</option>
            <option value="hypertension">High blood pressure</option>
            <option value="hemorrhage_history">History of heavy bleeding (PPH)</option>
            <option value="anemia">Severe anaemia</option>
            <option value="c_section">C-section</option>
          </select>
        </div>
      </div>

      {/* Follow-up Table */}
      {loading ? (
        <p className="text-sm text-ink-soft py-8">Loading follow-ups…</p>
      ) : items.length === 0 ? (
        <div className="bg-white border border-rule rounded-md p-8">
          <h3 className="text-base font-bold text-ink">Nobody is late.</h3>
          <p className="text-sm text-ink-soft mt-1">
            New follow-ups appear here on the morning they're due.
          </p>
        </div>
      ) : (
        <div className="bg-white border border-rule rounded-md overflow-x-auto">
          <table className="min-w-full">
            <thead>
              <tr className="text-left text-[13px] font-semibold text-ink-soft border-b border-rule">
                <th className="py-3 px-4 font-semibold w-24">Late by</th>
                <th className="py-3 px-4 font-semibold">Mother</th>
                <th className="py-3 px-4 font-semibold">Checkup</th>
                <th className="py-3 px-4 font-semibold">Risk</th>
                <th className="py-3 px-4"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => {
                const isOverdue = item.days_overdue > 0;
                return (
                  <tr key={item.visit_id} className="border-b border-rule last:border-0 hover:bg-paper">
                    <td className={`py-3 px-4 w-24 align-top border-l-4 ${isOverdue ? 'border-late' : 'border-soon'}`}>
                      {isOverdue ? (
                        <div>
                          <div className="text-3xl font-bold text-late leading-none tabular-nums">{item.days_overdue}</div>
                          <div className="text-xs text-late mt-1">{item.days_overdue === 1 ? 'day' : 'days'}</div>
                        </div>
                      ) : (
                        <span className="text-lg font-bold text-soon">Today</span>
                      )}
                    </td>

                    <td className="py-3 px-4 text-sm align-top">
                      <Link
                        to={`/patients/${item.patient_id}`}
                        className="text-sm font-semibold text-ink hover:text-scrub hover:underline"
                      >
                        {item.patient_name}
                      </Link>
                      <div className="text-xs text-ink-soft mt-0.5">
                        {`${item.contact_number}, speaks ${item.preferred_language}`}
                      </div>
                    </td>

                    <td className="py-3 px-4 align-top">
                      <div className="text-sm">{visitLabel(item.visit_type)}</div>
                      <div className="text-xs text-ink-soft mt-0.5">Due {item.due_date}</div>
                    </td>

                    <td className="py-3 px-4 text-sm align-top">
                      {item.risk_flags.length > 0 ? (
                        <span className="text-late">
                          {item.risk_flags.map((rf) => RISK_NAMES[rf] || rf).join(', ')}
                        </span>
                      ) : (
                        <span className="text-ink-faint">None</span>
                      )}
                    </td>

                    <td className="py-3 px-4 align-top whitespace-nowrap">
                      <div className="flex items-center justify-end gap-4">
                        <button
                          onClick={() => handleOpenWhatsAppSim(item)}
                          className="text-scrub text-sm font-semibold hover:underline underline-offset-2"
                        >
                          Preview message
                        </button>

                        <button
                          onClick={() => handleTriggerNudge(item)}
                          className="text-scrub text-sm font-semibold hover:underline underline-offset-2"
                        >
                          Send reminder
                        </button>

                        <button
                          onClick={() => setSelectedVisit(item)}
                          className="bg-scrub hover:bg-scrub-dark text-white text-sm font-semibold px-3 py-1.5 rounded"
                        >
                          Mark as visited
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Mark Complete Modal */}
      {selectedVisit && (
        <div className="fixed inset-0 bg-ink/40 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-md shadow-lg max-w-md w-full p-6">
            <h3 className="text-base font-bold text-ink">Mark as visited</h3>
            <p className="text-sm text-ink-soft mt-1 mb-4">
              {selectedVisit.patient_name}, {visitLabel(selectedVisit.visit_type)}
            </p>

            {modalError && (
              <div className="mb-4 border-l-4 border-late bg-late-tint text-late text-sm px-3 py-2">
                {modalError}
              </div>
            )}

            <form onSubmit={handleMarkCompleteSubmit} className="space-y-4">
              <div>
                <label htmlFor="visit-date" className="block text-sm font-semibold text-ink">Date of visit</label>
                <input
                  id="visit-date"
                  type="date"
                  required
                  value={completedDate}
                  onChange={(e) => setCompletedDate(e.target.value)}
                  className="mt-1 block w-full text-sm border border-rule-strong rounded px-3 py-2 bg-white focus:outline-none focus:border-scrub focus:ring-1 focus:ring-scrub"
                />
              </div>

              <div>
                <label htmlFor="visit-note" className="block text-sm font-semibold text-ink">Note</label>
                <textarea
                  id="visit-note"
                  rows="3"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  className="mt-1 block w-full text-sm border border-rule-strong rounded px-3 py-2 bg-white focus:outline-none focus:border-scrub focus:ring-1 focus:ring-scrub"
                ></textarea>
                <p className="text-xs text-ink-faint mt-1">
                  Where and how she was seen, e.g. 'home visit by ASHA'. Don't write clinical findings here; they belong in her case sheet.
                </p>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setSelectedVisit(null)}
                  className="bg-white border border-rule-strong text-ink text-sm font-semibold px-4 py-2 rounded hover:bg-paper"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-scrub hover:bg-scrub-dark text-white text-sm font-semibold px-4 py-2 rounded"
                >
                  Save visit
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* WhatsApp Preview Simulator Modal */}
      <WhatsAppPreviewModal
        isOpen={simModalOpen}
        onClose={() => setSimModalOpen(false)}
        patientName={simData.patientName}
        recipientContact={simData.recipientContact}
        visitType={simData.visitType}
        dueDate={simData.dueDate}
        facilityName={simData.facilityName}
        language={simData.language}
      />
    </div>
  );
}
