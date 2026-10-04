import { useState } from 'react';
import { errorMessage, visitApi } from '../api/client';
import { todayISO } from '../lib/format';
import { MISSED_REASONS, visitLabel } from '../lib/labels';
import { ErrorBanner } from './Feedback';
import Modal from './Modal';

// Record the outcome of one visit: done (FR-006) or missed (FR-007).
export default function VisitActionModal({ visit, patientName, onClose, onSaved }) {
  const [outcome, setOutcome] = useState('completed');
  const [completedDate, setCompletedDate] = useState(todayISO());
  const [note, setNote] = useState('');
  const [reason, setReason] = useState(MISSED_REASONS[0].value);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);
    try {
      if (outcome === 'completed') {
        await visitApi.markComplete(visit.visit_id, completedDate, note.trim());
      } else {
        await visitApi.markMissed(visit.visit_id, reason);
      }
      onSaved(outcome);
    } catch (err) {
      setError(errorMessage(err, "Couldn't save this visit."));
      setSaving(false);
    }
  };

  return (
    <Modal title="Record visit" subtitle={`${patientName}, ${visitLabel(visit.visit_type)}`} onClose={onClose}>
      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <fieldset>
          <legend className="label">What happened?</legend>
          <div className="flex gap-2">
            {[
              ['completed', 'She was seen'],
              ['missed', "It didn't happen"],
            ].map(([value, text]) => (
              <label
                key={value}
                className={`flex-1 border rounded px-3 py-2 text-sm font-semibold cursor-pointer text-center ${
                  outcome === value ? 'border-scrub bg-scrub-tint text-scrub-dark' : 'border-rule-strong text-ink-soft'
                }`}
              >
                <input
                  type="radio"
                  name="outcome"
                  value={value}
                  checked={outcome === value}
                  onChange={() => setOutcome(value)}
                  className="sr-only"
                />
                {text}
              </label>
            ))}
          </div>
        </fieldset>

        {outcome === 'completed' ? (
          <>
            <div>
              <label htmlFor="visit-date" className="label">
                Date of visit
              </label>
              <input
                id="visit-date"
                type="date"
                required
                max={todayISO()}
                value={completedDate}
                onChange={(e) => setCompletedDate(e.target.value)}
                className="field"
              />
            </div>
            <div>
              <label htmlFor="visit-note" className="label">
                Note <span className="font-normal text-ink-faint">(optional)</span>
              </label>
              <textarea
                id="visit-note"
                rows="3"
                maxLength={500}
                value={note}
                onChange={(e) => setNote(e.target.value)}
                placeholder="Home visit by ASHA worker"
                className="field"
              />
              <p className="hint">
                Where and how she was seen. Clinical findings belong in her case sheet; Cara rejects them here.
              </p>
            </div>
          </>
        ) : (
          <div>
            <label htmlFor="missed-reason" className="label">
              Reason
            </label>
            <select id="missed-reason" value={reason} onChange={(e) => setReason(e.target.value)} className="field">
              {MISSED_REASONS.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
