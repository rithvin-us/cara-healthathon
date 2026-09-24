import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { patientApi } from '../api/client';
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
      alert(`Discharge plan created for ${res.data.patient.name}.`);
      navigate('/worklist');
    } catch (err) {
      setError(err.response?.data?.detail || "Couldn't create the discharge plan. Check the details and try again.");
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
        { type: 'Week 1 risk check', date: addDays(delDateObj, 7) },
        { type: 'Week 2 risk check', date: addDays(delDateObj, 14) },
        { type: 'Week 3 risk check', date: addDays(delDateObj, 21) },
        { type: 'Week 4 risk check', date: addDays(delDateObj, 28) },
        { type: '6-week checkup', date: addDays(delDateObj, 42) },
      ];
    }

    return [
      { type: '24-hour checkup', date: addDays(delDateObj, 1) },
      { type: '3-day checkup', date: addDays(delDateObj, 3) },
      { type: '10-day checkup', date: addDays(delDateObj, 10) },
      { type: '6-week checkup', date: addDays(delDateObj, 42) },
    ];
  };

  const previewVisits = getPreviewVisits();

  const labelClass = 'block text-sm font-semibold text-ink mb-1';
  const inputClass =
    'block w-full text-sm border border-rule-strong rounded px-3 py-2 bg-white focus:outline-none focus:border-scrub focus:ring-1 focus:ring-scrub';
  const hintClass = 'text-xs text-ink-faint mt-1';

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-ink">
      <div>
        <h1 className="text-2xl font-bold text-ink">New discharge</h1>
        <p className="text-sm text-ink-soft mt-1">
          Add the mother and baby. Cara schedules her checkups from the discharge date.
        </p>
      </div>

      {error && (
        <div className="mt-6 border-l-4 border-late bg-late-tint text-late text-sm px-3 py-2">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="mt-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 max-w-2xl">
          <fieldset>
            <legend className="mb-4">
              <h2 className="text-base font-bold text-ink">Mother</h2>
            </legend>
            <div className="space-y-4">
              <div>
                <label htmlFor="mother-name" className={labelClass}>Full name</label>
                <input
                  id="mother-name"
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Sunita Rao"
                  className={inputClass}
                />
              </div>

              <div>
                <label htmlFor="mother-phone" className={labelClass}>Phone number</label>
                <input
                  id="mother-phone"
                  type="text"
                  required
                  value={contactNumber}
                  onChange={(e) => setContactNumber(e.target.value)}
                  placeholder="+919876543210"
                  className={inputClass}
                />
                <p className={hintClass}>WhatsApp and SMS reminders go to this number.</p>
              </div>

              <div>
                <label htmlFor="mother-language" className={labelClass}>Language</label>
                <select
                  id="mother-language"
                  value={preferredLanguage}
                  onChange={(e) => setPreferredLanguage(e.target.value)}
                  className={inputClass}
                >
                  <option value="English">English</option>
                  <option value="Hindi">Hindi</option>
                  <option value="Marathi">Marathi</option>
                  <option value="Gujarati">Gujarati</option>
                  <option value="Tamil">Tamil</option>
                </select>
                <p className={hintClass}>Reminders are sent in this language.</p>
              </div>
            </div>
          </fieldset>

          <div className="border-t border-rule pt-6 mt-8">
            <fieldset>
              <legend className="mb-4">
                <h2 className="text-base font-bold text-ink">Baby</h2>
              </legend>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="baby-name" className={labelClass}>Name</label>
                  <input
                    id="baby-name"
                    type="text"
                    value={newbornName}
                    onChange={(e) => setNewbornName(e.target.value)}
                    className={inputClass}
                  />
                  <p className={hintClass}>Leave blank if not named yet.</p>
                </div>

                <div>
                  <label htmlFor="baby-sex" className={labelClass}>Sex</label>
                  <select
                    id="baby-sex"
                    value={newbornGender}
                    onChange={(e) => setNewbornGender(e.target.value)}
                    className={inputClass}
                  >
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                  </select>
                </div>
              </div>
            </fieldset>
          </div>

          <div className="border-t border-rule pt-6 mt-8">
            <fieldset>
              <legend className="mb-4">
                <h2 className="text-base font-bold text-ink">Discharge</h2>
              </legend>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="delivery-date" className={labelClass}>Delivery date</label>
                  <input
                    id="delivery-date"
                    type="date"
                    required
                    value={deliveryDate}
                    onChange={(e) => setDeliveryDate(e.target.value)}
                    className={inputClass}
                  />
                </div>

                <div>
                  <label htmlFor="discharge-date" className={labelClass}>Discharge date</label>
                  <input
                    id="discharge-date"
                    type="date"
                    required
                    value={dischargeDate}
                    onChange={(e) => setDischargeDate(e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>
            </fieldset>
          </div>

          <div className="border-t border-rule pt-6 mt-8">
            <h2 className="text-base font-bold text-ink">Checkups Cara will schedule</h2>
            <div className="mt-4 bg-white border border-rule rounded-md">
              <table className="w-full">
                <thead>
                  <tr className="text-left text-[13px] font-semibold text-ink-soft border-b border-rule">
                    <th className="py-2 px-4 font-semibold">Checkup</th>
                    <th className="py-2 px-4 font-semibold">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {previewVisits.map((v, i) => (
                    <tr key={i} className="border-b border-rule last:border-0">
                      <td className="py-3 px-4 text-sm text-ink">{v.type}</td>
                      <td className="py-3 px-4 text-sm text-ink-soft">{v.date}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="border-t border-rule pt-6 mt-8 flex justify-end gap-3">
            <button
              type="button"
              onClick={() => navigate('/worklist')}
              className="bg-white border border-rule-strong text-ink text-sm font-semibold px-4 py-2 rounded hover:bg-paper"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={loading}
              className="bg-scrub hover:bg-scrub-dark text-white text-sm font-semibold px-4 py-2 rounded disabled:opacity-60"
            >
              {loading ? 'Creating…' : 'Create discharge plan'}
            </button>
          </div>
        </div>

        <div className="border-t border-rule pt-6 lg:border-0 lg:pt-0">
          <fieldset>
            <legend className="mb-4">
              <h2 className="text-base font-bold text-ink">Risk</h2>
            </legend>
            <FOGSIRiskCalculator onSelectRiskFlags={(flags) => setSelectedRiskFlags(flags)} />
          </fieldset>
        </div>
      </form>
    </div>
  );
}
