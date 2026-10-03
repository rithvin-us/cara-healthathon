import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { errorMessage, visitApi, worklistApi } from '../api/client';
import { ErrorBanner, Loading, PageShell } from '../components/Feedback';
import { useToast } from '../components/Toast';
import VisitActionModal from '../components/VisitActionModal';
import WhatsAppPreviewModal from '../components/WhatsAppPreviewModal';
import { useApp } from '../context/AppContext';
import { formatDate, formatPhone, timeAgo } from '../lib/format';
import { DEFAULT_VISIT_TYPES, RISK_LABELS, riskLabel, visitLabel } from '../lib/labels';

function SummaryStat({ label, value, tone = 'text-ink' }) {
  return (
    <div className="pr-6 sm:pr-8">
      <dt className="text-sm text-ink-soft">{label}</dt>
      <dd className={`text-2xl font-bold tabular-nums ${tone}`}>{value}</dd>
    </div>
  );
}

function LastReminder({ at, status }) {
  if (!at) return <span className="text-ink-faint">No reminder yet</span>;
  if (status === 'failed') return <span className="text-late font-semibold">Reminder failed, call her</span>;
  return (
    <span className="text-ink-soft">
      Reminded {timeAgo(at)}
      {status === 'read' ? ', read' : ''}
    </span>
  );
}

export default function Worklist() {
  const { dataVersion } = useApp();
  const toast = useToast();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [visitTypeFilter, setVisitTypeFilter] = useState('');
  const [riskFlagFilter, setRiskFlagFilter] = useState('');
  const [recording, setRecording] = useState(null);
  const [previewing, setPreviewing] = useState(null);
  const [sendingId, setSendingId] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await worklistApi.get(visitTypeFilter, riskFlagFilter);
      setData(res.data);
    } catch (err) {
      setError(errorMessage(err, "Couldn't load the follow-up list."));
    } finally {
      setLoading(false);
    }
  }, [visitTypeFilter, riskFlagFilter]);

  useEffect(() => {
    load();
  }, [load, dataVersion]);

  const sendReminder = async (item) => {
    setSendingId(item.visit_id);
    try {
      const res = await visitApi.sendReminder(item.visit_id);
      const sent = res.data.filter((n) => n.status !== 'failed').length;
      if (sent === res.data.length) {
        const family = sent - 1;
        const extra = family > 0 ? ` and ${family} family ${family === 1 ? 'member' : 'members'}` : '';
        toast.success(`WhatsApp reminder sent to ${item.patient_name}${extra}.`);
      } else {
        toast.error(`${res.data.length - sent} of ${res.data.length} reminders failed. Call ${item.patient_name}.`);
      }
      load();
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't send the reminder."));
    } finally {
      setSendingId(null);
    }
  };

  const items = data?.items || [];
  const filtered = visitTypeFilter || riskFlagFilter;

  return (
    <PageShell>
      <div className="md:flex md:items-start md:justify-between gap-6">
        <div>
          <h1 className="text-2xl font-bold">Follow-ups</h1>
          <p className="text-sm text-ink-soft mt-1">
            Mothers due or late for a checkup{data ? `, as of ${formatDate(data.as_of)}` : ''}. Most overdue first.
          </p>
        </div>
        <button type="button" onClick={load} className="btn-secondary mt-4 md:mt-0" disabled={loading}>
          Refresh
        </button>
      </div>

      {data && (
        <dl className="mt-6 flex flex-wrap gap-y-4 divide-x divide-rule [&>div]:pl-6 sm:[&>div]:pl-8 [&>div:first-child]:pl-0">
          <SummaryStat label="Overdue" value={data.summary.overdue} tone="text-late" />
          <SummaryStat label="Due today" value={data.summary.due_today} tone="text-soon" />
          <SummaryStat label="High-risk mothers" value={data.summary.high_risk} />
          <SummaryStat label="Due in the next 7 days" value={data.summary.upcoming_7_days} />
        </dl>
      )}

      <div className="mt-8 mb-4 flex flex-col gap-4 md:flex-row md:items-end md:gap-6">
        <div className="md:w-56">
          <label htmlFor="visit-filter" className="label">
            Visit
          </label>
          <select
            id="visit-filter"
            value={visitTypeFilter}
            onChange={(e) => setVisitTypeFilter(e.target.value)}
            className="field"
          >
            <option value="">All visits</option>
            {DEFAULT_VISIT_TYPES.map((t) => (
              <option key={t} value={t}>
                {visitLabel(t)}
              </option>
            ))}
          </select>
        </div>
        <div className="md:w-56">
          <label htmlFor="risk-filter" className="label">
            Risk
          </label>
          <select
            id="risk-filter"
            value={riskFlagFilter}
            onChange={(e) => setRiskFlagFilter(e.target.value)}
            className="field"
          >
            <option value="">All mothers</option>
            {Object.entries(RISK_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>
        {filtered && (
          <button
            type="button"
            className="btn-link md:pb-2"
            onClick={() => {
              setVisitTypeFilter('');
              setRiskFlagFilter('');
            }}
          >
            Clear filters
          </button>
        )}
      </div>

      {error && <ErrorBanner message={error} onRetry={load} />}

      {loading && !data ? (
        <Loading label="Loading follow-ups…" />
      ) : !error && items.length === 0 ? (
        <div className="card p-8">
          <h2 className="text-base font-bold">{filtered ? 'Nobody matches these filters.' : 'Nobody is due or late.'}</h2>
          <p className="text-sm text-ink-soft mt-1">
            {filtered
              ? 'Clear the filters to see every mother who needs a call.'
              : "Mothers appear here on the morning a checkup is due, and stay until it's recorded."}
          </p>
        </div>
      ) : (
        items.length > 0 && (
          <div className={`card overflow-x-auto ${loading ? 'opacity-60' : ''}`}>
            <table className="min-w-full">
              <thead>
                <tr className="border-b border-rule">
                  <th className="th w-24">Late by</th>
                  <th className="th">Mother</th>
                  <th className="th">Checkup</th>
                  <th className="th">Risk</th>
                  <th className="th">
                    <span className="sr-only">Actions</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => {
                  const late = item.days_overdue > 0;
                  return (
                    <tr key={item.visit_id} className="border-b border-rule last:border-0 hover:bg-paper">
                      <td className={`py-3 px-4 w-24 align-top border-l-4 ${late ? 'border-late' : 'border-soon'}`}>
                        {late ? (
                          <>
                            <div className="text-3xl font-bold text-late leading-none tabular-nums">
                              {item.days_overdue}
                            </div>
                            <div className="text-xs text-late mt-1">{item.days_overdue === 1 ? 'day' : 'days'}</div>
                          </>
                        ) : (
                          <span className="text-lg font-bold text-soon">Today</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-sm align-top">
                        <Link
                          to={`/patients/${item.patient_id}`}
                          className="font-semibold text-ink hover:text-scrub hover:underline"
                        >
                          {item.patient_name}
                        </Link>
                        <div className="text-xs text-ink-soft mt-0.5">
                          {formatPhone(item.contact_number)} · {item.preferred_language}
                        </div>
                        <div className="text-xs mt-0.5">
                          <LastReminder at={item.last_reminder_at} status={item.last_reminder_status} />
                        </div>
                      </td>
                      <td className="py-3 px-4 align-top">
                        <div className="text-sm">{visitLabel(item.visit_type)}</div>
                        <div className="text-xs text-ink-soft mt-0.5">Due {formatDate(item.due_date)}</div>
                      </td>
                      <td className="py-3 px-4 text-sm align-top">
                        {item.risk_flags.length > 0 ? (
                          <span className="text-late">{item.risk_flags.map(riskLabel).join(', ')}</span>
                        ) : (
                          <span className="text-ink-faint">None</span>
                        )}
                      </td>
                      <td className="py-3 px-4 align-top whitespace-nowrap">
                        <div className="flex items-center justify-end gap-4">
                          <button type="button" onClick={() => setPreviewing(item)} className="btn-link">
                            Preview
                          </button>
                          <button
                            type="button"
                            onClick={() => sendReminder(item)}
                            className="btn-link"
                            disabled={sendingId === item.visit_id}
                          >
                            {sendingId === item.visit_id ? 'Sending…' : 'Send reminder'}
                          </button>
                          <button type="button" onClick={() => setRecording(item)} className="btn-primary py-1.5 px-3">
                            Record visit
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )
      )}

      {recording && (
        <VisitActionModal
          visit={recording}
          patientName={recording.patient_name}
          onClose={() => setRecording(null)}
          onSaved={(outcome) => {
            toast.success(
              outcome === 'completed'
                ? `${recording.patient_name}'s ${visitLabel(recording.visit_type)} is recorded as done.`
                : `${recording.patient_name}'s ${visitLabel(recording.visit_type)} is recorded as missed.`,
            );
            setRecording(null);
            load();
          }}
        />
      )}

      {previewing && (
        <WhatsAppPreviewModal
          visitId={previewing.visit_id}
          onClose={() => setPreviewing(null)}
          onSend={() => sendReminder(previewing)}
        />
      )}
    </PageShell>
  );
}
