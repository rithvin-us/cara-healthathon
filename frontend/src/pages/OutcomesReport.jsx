import { useCallback, useEffect, useState } from 'react';
import { errorMessage, reportApi } from '../api/client';
import { ErrorBanner, Loading, PageShell } from '../components/Feedback';
import { useToast } from '../components/Toast';
import { useApp } from '../context/AppContext';
import { visitLabel } from '../lib/labels';

function Stat({ label, value, note, tone = 'text-ink' }) {
  return (
    <div>
      <dt className="text-sm text-ink-soft">{label}</dt>
      <dd className={`text-2xl font-bold tabular-nums ${tone}`}>{value}</dd>
      {note && <dd className="text-xs text-ink-faint">{note}</dd>}
    </div>
  );
}

export default function OutcomesReport() {
  const { user, dataVersion } = useApp();
  const toast = useToast();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [anonymize, setAnonymize] = useState(true);
  const [downloading, setDownloading] = useState(false);

  const isAdmin = user?.role === 'Admin';
  const rangeInvalid = startDate && endDate && startDate > endDate;

  const load = useCallback(async () => {
    if (rangeInvalid) return;
    setLoading(true);
    setError('');
    try {
      const res = await reportApi.getOutcomes(startDate, endDate);
      setData(res.data);
    } catch (err) {
      setError(errorMessage(err, "Couldn't load the report."));
    } finally {
      setLoading(false);
    }
  }, [startDate, endDate, rangeInvalid]);

  useEffect(() => {
    load();
  }, [load, dataVersion]);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const res = await reportApi.downloadCsv(startDate, endDate, anonymize || !isAdmin);
      const url = window.URL.createObjectURL(new Blob([res.data], { type: 'text/csv' }));
      const link = document.createElement('a');
      link.href = url;
      link.download = anonymize || !isAdmin ? 'cara_outcomes_anonymised.csv' : 'cara_outcomes_report.csv';
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success('CSV downloaded.');
    } catch (err) {
      // Blob responses hide the JSON error body; read it back for the message.
      let message = errorMessage(err, "Couldn't download the CSV.");
      if (err.response?.data instanceof Blob) {
        try {
          message = JSON.parse(await err.response.data.text()).detail || message;
        } catch {
          /* keep the generic message */
        }
      }
      toast.error(message);
    } finally {
      setDownloading(false);
    }
  };

  return (
    <PageShell>
      <div className="md:flex md:items-start md:justify-between gap-6">
        <div>
          <h1 className="text-2xl font-bold">Reports</h1>
          <p className="text-sm text-ink-soft mt-1">Checkups due versus checkups done, by visit.</p>
        </div>
        <div className="mt-4 md:mt-0 flex items-center gap-4">
          {isAdmin ? (
            <label htmlFor="anonymize" className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                id="anonymize"
                checked={anonymize}
                onChange={(e) => setAnonymize(e.target.checked)}
                className="h-4 w-4 accent-[#0E5A54]"
              />
              Remove names and numbers
            </label>
          ) : (
            <span className="text-xs text-ink-faint">Export is anonymised</span>
          )}
          <button type="button" onClick={handleDownload} className="btn-secondary" disabled={downloading || rangeInvalid}>
            {downloading ? 'Preparing…' : 'Download CSV'}
          </button>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-end gap-4">
        <div className="w-44">
          <label htmlFor="from" className="label">
            Due from
          </label>
          <input id="from" type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="field" />
        </div>
        <div className="w-44">
          <label htmlFor="to" className="label">
            Due to
          </label>
          <input id="to" type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="field" />
        </div>
        {(startDate || endDate) && (
          <button
            type="button"
            onClick={() => {
              setStartDate('');
              setEndDate('');
            }}
            className="btn-link py-2"
          >
            All dates
          </button>
        )}
      </div>

      {rangeInvalid && (
        <div className="mt-6">
          <ErrorBanner message="The start date must be on or before the end date." />
        </div>
      )}
      {error && (
        <div className="mt-6">
          <ErrorBanner message={error} onRetry={load} />
        </div>
      )}

      {loading && !data ? (
        <Loading />
      ) : (
        data && (
          <div className={loading ? 'opacity-60' : ''}>
            <dl className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-6">
              <Stat
                label="Checkups done"
                value={`${data.overall_completion_rate_pct}%`}
                note={`${data.completed_visits} of ${data.total_visits} visits`}
              />
              <Stat label="Mothers followed up" value={data.total_patients} />
              <Stat label="Overdue now" value={data.overdue_visits} tone="text-late" />
              <Stat label="Missed" value={data.missed_visits} note="Couldn't reach, declined or moved" />
            </dl>

            <section className="border-t border-rule pt-6 mt-8">
              <h2 className="text-base font-bold">By visit</h2>
              {data.outcomes_by_visit_type.length === 0 ? (
                <p className="text-sm text-ink-soft mt-3">No checkups were due in this date range.</p>
              ) : (
                <div className="mt-4 card overflow-x-auto">
                  <table className="min-w-full">
                    <thead>
                      <tr className="border-b border-rule">
                        <th className="th">Visit</th>
                        <th className="th text-right">Scheduled</th>
                        <th className="th text-right">Done</th>
                        <th className="th text-right">Missed</th>
                        <th className="th text-right">Overdue</th>
                        <th className="th">Completion</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.outcomes_by_visit_type.map((row) => (
                        <tr key={row.visit_type} className="border-b border-rule last:border-0 hover:bg-paper">
                          <td className="py-3 px-4 text-sm font-semibold">{visitLabel(row.visit_type)}</td>
                          <td className="py-3 px-4 text-sm text-right tabular-nums">{row.total}</td>
                          <td className="py-3 px-4 text-sm text-right tabular-nums">{row.completed}</td>
                          <td className="py-3 px-4 text-sm text-right tabular-nums">{row.missed}</td>
                          <td
                            className={`py-3 px-4 text-sm text-right tabular-nums ${row.overdue > 0 ? 'text-late font-semibold' : ''}`}
                          >
                            {row.overdue}
                          </td>
                          <td className="py-3 px-4 text-sm">
                            <div className="flex items-center gap-3">
                              <div className="w-24 bg-rule h-1.5 rounded-sm overflow-hidden" aria-hidden="true">
                                <div className="bg-scrub h-1.5" style={{ width: `${row.completion_rate_pct}%` }} />
                              </div>
                              <span className="tabular-nums">{row.completion_rate_pct}%</span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
              <p className="text-xs text-ink-faint mt-3">
                Counts checkups that were due on or before today. Upcoming checkups aren't included.
              </p>
            </section>
          </div>
        )
      )}
    </PageShell>
  );
}
