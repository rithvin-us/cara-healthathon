import React, { useState, useEffect } from 'react';
import { reportApi } from '../api/client';
import { visitLabel } from '../labels';

export default function OutcomesReport() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [anonymize, setAnonymize] = useState(true);

  const loadReport = async () => {
    setLoading(true);
    try {
      const res = await reportApi.getOutcomes(startDate, endDate);
      setData(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [startDate, endDate]);

  const handleDownloadCsv = async () => {
    try {
      const res = await reportApi.downloadCsv(startDate, endDate, anonymize);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', anonymize ? 'cara_anonymised_outcomes.csv' : 'cara_outcomes_report.csv');
      document.body.appendChild(link);
      link.click();
      link.remove();
    } catch (err) {
      alert("Couldn't download CSV: " + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="md:flex md:items-start md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-ink">Reports</h1>
          <p className="text-sm text-ink-soft mt-1">
            How many checkups were done on time, by visit.
          </p>
        </div>

        <div className="mt-4 md:mt-0 flex items-center gap-4">
          <label htmlFor="anonymize_check" className="flex items-center gap-2 text-sm text-ink">
            <input
              type="checkbox"
              id="anonymize_check"
              checked={anonymize}
              onChange={(e) => setAnonymize(e.target.checked)}
              className="h-4 w-4 accent-scrub"
            />
            Anonymise the CSV
          </label>

          <button
            onClick={handleDownloadCsv}
            className="bg-white border border-rule-strong text-ink text-sm font-semibold px-4 py-2 rounded hover:bg-paper"
          >
            Download CSV
          </button>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap items-end gap-4">
        <div className="w-44">
          <label className="text-sm font-semibold text-ink">From</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="mt-1 block w-full text-sm border border-rule-strong rounded px-3 py-2 bg-white focus:outline-none focus:border-scrub focus:ring-1 focus:ring-scrub"
          />
        </div>
        <div className="w-44">
          <label className="text-sm font-semibold text-ink">To</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="mt-1 block w-full text-sm border border-rule-strong rounded px-3 py-2 bg-white focus:outline-none focus:border-scrub focus:ring-1 focus:ring-scrub"
          />
        </div>

        <button
          onClick={() => {
            setStartDate('');
            setEndDate('');
          }}
          className="text-scrub text-sm font-semibold hover:underline underline-offset-2 py-2"
        >
          Clear dates
        </button>
      </div>

      {loading ? (
        <p className="mt-8 text-sm text-ink-soft">Loading…</p>
      ) : !data ? (
        <p className="mt-8 text-sm text-ink-soft">
          No report data for these dates. Try clearing the date range.
        </p>
      ) : (
        <>
          <dl className="mt-8 flex flex-wrap divide-x divide-rule">
            <div className="pr-8">
              <dt className="text-sm text-ink-soft">Checkups done</dt>
              <dd className="text-2xl font-bold tabular-nums text-ink">
                {data.overall_completion_rate_pct}%
              </dd>
              <dd className="text-xs text-ink-faint">
                {data.completed_visits} of {data.total_visits} visits
              </dd>
            </div>

            <div className="px-8">
              <dt className="text-sm text-ink-soft">Mothers followed up</dt>
              <dd className="text-2xl font-bold tabular-nums text-ink">{data.total_patients}</dd>
            </div>

            <div className="px-8">
              <dt className="text-sm text-ink-soft">Overdue now</dt>
              <dd className="text-2xl font-bold tabular-nums text-late">{data.overdue_visits}</dd>
            </div>

            <div className="pl-8">
              <dt className="text-sm text-ink-soft">Missed or couldn't reach</dt>
              <dd className="text-2xl font-bold tabular-nums text-ink">{data.missed_visits}</dd>
            </div>
          </dl>

          <div className="border-t border-rule pt-6 mt-8">
            <h2 className="text-base font-bold text-ink">By visit</h2>

            <div className="mt-4 bg-white border border-rule rounded-md overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="text-left text-[13px] font-semibold text-ink-soft border-b border-rule">
                    <th className="py-3 px-4 font-semibold">Visit</th>
                    <th className="py-3 px-4 font-semibold text-right">Scheduled</th>
                    <th className="py-3 px-4 font-semibold text-right">Done</th>
                    <th className="py-3 px-4 font-semibold text-right">Overdue</th>
                    <th className="py-3 px-4 font-semibold">Done on time</th>
                  </tr>
                </thead>
                <tbody>
                  {data.outcomes_by_visit_type.map((row, i) => (
                    <tr key={i} className="border-b border-rule last:border-0 hover:bg-paper">
                      <td className="py-3 px-4 text-sm font-semibold text-ink">{visitLabel(row.visit_type)}</td>
                      <td className="py-3 px-4 text-sm text-right tabular-nums text-ink">{row.total}</td>
                      <td className="py-3 px-4 text-sm text-right tabular-nums text-ink">{row.completed}</td>
                      <td className={`py-3 px-4 text-sm text-right tabular-nums ${row.overdue > 0 ? 'text-late font-semibold' : 'text-ink'}`}>
                        {row.overdue}
                      </td>
                      <td className="py-3 px-4 text-sm">
                        <div className="flex items-center gap-3">
                          <div className="w-24 bg-rule h-1.5 rounded-sm overflow-hidden">
                            <div
                              className="bg-scrub h-1.5 rounded-sm"
                              style={{ width: `${row.completion_rate_pct}%` }}
                            ></div>
                          </div>
                          <span className="tabular-nums text-ink">{row.completion_rate_pct}%</span>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
