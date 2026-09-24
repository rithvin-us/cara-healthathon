import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientApi } from '../api/client';
import { Calendar, User, Phone, Globe, ShieldAlert, CheckCircle, ArrowRight, Activity, Stethoscope } from 'lucide-react';
import FOGSIRiskCalculator from '../components/FOGSIRiskCalculator';

export default function NewDischargePlan() {
  const navigate = useNavigate();

  const todayStr = new Date().toISOString().split('T')[0];
  const [name, setName] = useState('');
  const [contactNumber, setContactNumber] = useState('');
  const [preferredLanguage, setPreferredLanguage] = useState('English');
  const [deliveryDate, setDeliveryDate] = useState(todayStr);
  const [dischargeDate, setDischargeDate] = useState(todayStr);
  const [newbornGender, setNewbornGender] = useState('Female');
  const [newbornName, setNewbornName] = useState('');
  const [selectedRiskFlags, setSelectedRiskFlags] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        name,
        contact_number: contactNumber,
        preferred_language: preferredLanguage,
        delivery_date: deliveryDate,
        discharge_date: dischargeDate,
        newborn_gender: newbornGender,
        newborn_name: newbornName,
        risk_flags: selectedRiskFlags,
      };

      const res = await patientApi.createPatient(payload);
      alert(`Discharge plan created successfully for ${res.data.patient.name}!`);
      navigate('/worklist');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create discharge plan.');
    } finally {
      setLoading(false);
    }
  };

  const getPreviewVisits = () => {
    if (!deliveryDate) return [];
    const delDateObj = new Date(deliveryDate);

    const addDays = (d, days) => {
      const copy = new Date(d);
      copy.setDate(copy.getDate() + days);
      return copy.toISOString().split('T')[0];
    };

    if (selectedRiskFlags.length > 0) {
      return [
        { type: 'Weekly Risk Checkup (Week 1)', date: addDays(delDateObj, 7) },
        { type: 'Weekly Risk Checkup (Week 2)', date: addDays(delDateObj, 14) },
        { type: 'Weekly Risk Checkup (Week 3)', date: addDays(delDateObj, 21) },
        { type: 'Weekly Risk Checkup (Week 4)', date: addDays(delDateObj, 28) },
        { type: '6wk Final PNC Checkup', date: addDays(delDateObj, 42) },
      ];
    }

    return [
      { type: '24h Checkup', date: addDays(delDateObj, 1) },
      { type: '48-72h Checkup', date: addDays(delDateObj, 3) },
      { type: '7-14d Checkup', date: addDays(delDateObj, 10) },
      { type: '6wk Checkup', date: addDays(delDateObj, 42) },
    ];
  };

  const previewVisits = getPreviewVisits();

  return (
    <div className="max-w-5xl mx-auto px-4 py-8 font-sans text-slate-900">
      <div className="mb-6 border-b border-slate-200 pb-4 flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Stethoscope className="h-6 w-6 text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">Create Postnatal Discharge Plan</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            FR-001 / FR-002: OBGYN clinical form. Calculates 4 WHO default/risk-modified follow-up visit dates.
          </p>
        </div>
        <span className="text-xs font-mono font-bold text-indigo-700 bg-indigo-50 px-2.5 py-1 rounded border border-indigo-200">
          Doctor Scope
        </span>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border-l-4 border-red-500 p-3 text-xs text-red-700 rounded-lg">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Mother Info Section */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-2xs space-y-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2 border-b border-slate-100 pb-3 uppercase tracking-wider text-xs">
            <User className="h-4 w-4 text-indigo-600" />
            <span>Mother & Intake Record</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-bold text-slate-700">Mother Full Name *</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Sunita Rao"
                className="mt-1 block w-full text-xs border border-slate-300 rounded-md p-2.5 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700">Contact Number (WhatsApp/SMS) *</label>
              <input
                type="text"
                required
                value={contactNumber}
                onChange={(e) => setContactNumber(e.target.value)}
                placeholder="+919876543210"
                className="mt-1 block w-full text-xs border border-slate-300 rounded-md p-2.5 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block font-bold text-slate-700">Preferred Nudge Language</label>
              <select
                value={preferredLanguage}
                onChange={(e) => setPreferredLanguage(e.target.value)}
                className="mt-1 block w-full text-xs border border-slate-300 rounded-md p-2.5 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
              >
                <option value="English">English</option>
                <option value="Hindi">Hindi</option>
                <option value="Marathi">Marathi</option>
                <option value="Gujarati">Gujarati</option>
                <option value="Tamil">Tamil</option>
              </select>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block font-bold text-slate-700">Delivery Date *</label>
                <input
                  type="date"
                  required
                  value={deliveryDate}
                  onChange={(e) => setDeliveryDate(e.target.value)}
                  className="mt-1 block w-full text-xs border border-slate-300 rounded-md p-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="block font-bold text-slate-700">Discharge Date *</label>
                <input
                  type="date"
                  required
                  value={dischargeDate}
                  onChange={(e) => setDischargeDate(e.target.value)}
                  className="mt-1 block w-full text-xs border border-slate-300 rounded-md p-2 focus:ring-indigo-500 focus:border-indigo-500"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Clinical FOGSI Gestosis Calculator */}
        <FOGSIRiskCalculator onSelectRiskFlags={(flags) => setSelectedRiskFlags(flags)} />

        {/* Generated Schedule Preview */}
        <div className="bg-slate-900 text-white p-6 rounded-xl border border-slate-800 shadow-2xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold text-white flex items-center space-x-2">
              <Calendar className="h-4 w-4 text-emerald-400" />
              <span>Computed PNC Visit Schedule ({previewVisits.length} Touchpoints)</span>
            </h3>
            <span className="text-[10px] font-mono bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded border border-emerald-800">
              WHO / FOGSI Rules Engine
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {previewVisits.map((v, i) => (
              <div key={i} className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex items-center justify-between">
                <div>
                  <div className="font-bold text-slate-100">{v.type}</div>
                  <div className="text-[11px] text-slate-400 font-mono">Scheduled: {v.date}</div>
                </div>
                <span className="text-[10px] font-bold bg-slate-800 text-slate-300 px-2 py-0.5 rounded">
                  Touchpoint #{i + 1}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end space-x-4 pt-2">
          <button
            type="button"
            onClick={() => navigate('/worklist')}
            className="px-4 py-2 text-xs font-semibold text-slate-600 bg-white border border-slate-300 hover:bg-slate-50 rounded-md shadow-2xs transition"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center space-x-1.5 px-5 py-2 text-xs font-bold text-white bg-indigo-600 hover:bg-indigo-700 rounded-md shadow-sm transition cursor-pointer"
          >
            <span>{loading ? 'Submitting...' : 'Finalize & Save Discharge Plan'}</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </div>
      </form>
    </div>
  );
}
