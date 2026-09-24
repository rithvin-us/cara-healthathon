import React, { useState, useEffect } from 'react';
import { reportApi } from '../api/client';
import { BarChart2, Download, Shield, Calendar, CheckCircle2, AlertTriangle, Clock } from 'lucide-react';

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
      alert('Error downloading CSV: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Facility Outcomes & Completion Report</h1>
          <p className="text-sm text-slate-600">
            FR-019 / FR-020: Aggregate PNC completion metrics with anonymized CSV export options for accreditation.
          </p>
        </div>

        <div className="mt-4 md:mt-0 flex items-center space-x-3">
          <div className="flex items-center space-x-2 bg-white px-3 py-1.5 rounded-lg border border-slate-300">
            <input
              type="checkbox"
              id="anonymize_check"
              checked={anonymize}
              onChange={(e) => setAnonymize(e.target.checked)}
              className="h-4 w-4 text-emerald-600 rounded"
            />
            <label htmlFor="anonymize_check" className="text-xs font-semibold text-slate-700 flex items-center">
              <Shield className="h-3.5 w-3.5 mr-1 text-emerald-700" />
              Anonymize Identifiers
            </label>
          </div>

          <button
            onClick={handleDownloadCsv}
            className="flex items-center space-x-1.5 px-4 py-2 bg-emerald-700 hover:bg-emerald-800 text-white rounded-lg text-sm font-semibold shadow-sm transition"
          >
            <Download className="h-4 w-4" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Date Filter Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center space-x-4">
        <span className="text-xs font-bold text-slate-700 uppercase flex items-center">
          <Calendar className="h-4 w-4 mr-1 text-emerald-700" />
          Filter Date Range:
        </span>

        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          className="text-xs border border-slate-300 rounded-lg p-1.5 focus:ring-emerald-500 focus:border-emerald-500"
        />
        <span className="text-slate-400 text-xs">to</span>
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          className="text-xs border border-slate-300 rounded-lg p-1.5 focus:ring-emerald-500 focus:border-emerald-500"
        />

        <button
          onClick={() => {
            setStartDate('');
            setEndDate('');
          }}
          className="text-xs text-slate-500 hover:text-slate-800 underline"
        >
          Reset Dates
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12 bg-white rounded-xl border border-slate-200">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-emerald-600 border-t-transparent"></div>
          <p className="mt-2 text-sm text-slate-500">Compiling report metrics...</p>
        </div>
      ) : !data ? (
        <div className="text-center py-12 text-slate-500">No data available.</div>
      ) : (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="text-xs font-bold text-slate-500 uppercase">Overall Completion Rate</div>
              <div className="text-3xl font-extrabold text-emerald-700 mt-2">
                {data.overall_completion_rate_pct}%
              </div>
              <div className="text-xs text-slate-400 mt-1">{data.completed_visits} of {data.total_visits} visits done</div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="text-xs font-bold text-slate-500 uppercase">Total Active Patients</div>
              <div className="text-3xl font-extrabold text-slate-900 mt-2">
                {data.total_patients}
              </div>
              <div className="text-xs text-slate-400 mt-1">Discharged mothers</div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="text-xs font-bold text-slate-500 uppercase">Currently Overdue</div>
              <div className="text-3xl font-extrabold text-rose-600 mt-2">
                {data.overdue_visits}
              </div>
              <div className="text-xs text-slate-400 mt-1">Requiring immediate contact</div>
            </div>

            <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
              <div className="text-xs font-bold text-slate-500 uppercase">Missed / Unreachable</div>
              <div className="text-3xl font-extrabold text-amber-600 mt-2">
                {data.missed_visits}
              </div>
              <div className="text-xs text-slate-400 mt-1">Operational reasons logged</div>
            </div>
          </div>

          {/* Breakdown by Visit Type */}
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
            <h3 className="text-base font-bold text-slate-900 border-b border-slate-100 pb-3 flex items-center space-x-2">
              <BarChart2 className="h-5 w-5 text-emerald-700" />
              <span>Completion Rate Breakdown by Visit Type</span>
            </h3>

            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-slate-200 text-sm">
                <thead className="bg-slate-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-bold text-slate-600 uppercase">Visit Type</th>
                    <th className="px-6 py-3 text-center text-xs font-bold text-slate-600 uppercase">Total Scheduled</th>
                    <th className="px-6 py-3 text-center text-xs font-bold text-slate-600 uppercase">Completed</th>
                    <th className="px-6 py-3 text-center text-xs font-bold text-slate-600 uppercase">Overdue</th>
                    <th className="px-6 py-3 text-right text-xs font-bold text-slate-600 uppercase">Completion Rate</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-slate-200">
                  {data.outcomes_by_visit_type.map((row, i) => (
                    <tr key={i} className="hover:bg-slate-50 transition">
                      <td className="px-6 py-4 font-bold text-slate-900">{row.visit_type}</td>
                      <td className="px-6 py-4 text-center font-medium">{row.total}</td>
                      <td className="px-6 py-4 text-center text-emerald-700 font-bold">{row.completed}</td>
                      <td className="px-6 py-4 text-center text-rose-600 font-bold">{row.overdue}</td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end space-x-2">
                          <div className="w-24 bg-slate-200 rounded-full h-2 overflow-hidden">
                            <div
                              className="bg-emerald-600 h-2 rounded-full"
                              style={{ width: `${row.completion_rate_pct}%` }}
                            ></div>
                          </div>
                          <span className="font-bold text-slate-900 text-xs">{row.completion_rate_pct}%</span>
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
