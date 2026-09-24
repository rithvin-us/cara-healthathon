import React, { useState } from 'react';
import { Activity, AlertTriangle, CheckCircle, Info } from 'lucide-react';

export default function FOGSIRiskCalculator({ onSelectRiskFlags }) {
  const [selectedCriteria, setSelectedCriteria] = useState([]);

  const criteriaList = [
    { id: 'hypertension', label: 'Gestational Hypertension / Preeclampsia', score: 3, riskFlag: 'hypertension' },
    { id: 'hemorrhage_history', label: 'Prior Postpartum Hemorrhage (PPH)', score: 3, riskFlag: 'hemorrhage_history' },
    { id: 'anemia', label: 'Severe Anemia (Hb < 8 g/dL)', score: 2, riskFlag: 'anemia' },
    { id: 'c_section', label: 'Emergency C-Section Delivery', score: 2, riskFlag: 'c_section' },
    { id: 'twins', label: 'Multiple Gestation (Twins/Triplets)', score: 2, riskFlag: 'other' },
    { id: 'diabetes', label: 'Gestational Diabetes Mellitus', score: 1, riskFlag: 'other' },
  ];

  const toggleCriteria = (id) => {
    let next;
    if (selectedCriteria.includes(id)) {
      next = selectedCriteria.filter((c) => c !== id);
    } else {
      next = [...selectedCriteria, id];
    }
    setSelectedCriteria(next);

    // Map to active risk flags
    const activeFlags = criteriaList
      .filter((c) => next.includes(c.id))
      .map((c) => c.riskFlag);
    
    // Remove duplicates
    const uniqueFlags = Array.from(new Set(activeFlags));
    onSelectRiskFlags(uniqueFlags);
  };

  const totalScore = criteriaList
    .filter((c) => selectedCriteria.includes(c.id))
    .reduce((sum, c) => sum + c.score, 0);

  let riskCategory = 'Standard Risk';
  let categoryColor = 'bg-emerald-50 text-emerald-800 border-emerald-300';
  let recommendation = 'Standard WHO 4-visit schedule (24h, 72h, 14d, 6wk).';

  if (totalScore >= 3) {
    riskCategory = 'High Risk Cadence';
    categoryColor = 'bg-rose-50 text-rose-900 border-rose-300';
    recommendation = 'Weekly visit cadence for 4 weeks + 6wk final checkup (FOGSI Protocol).';
  } else if (totalScore >= 1) {
    riskCategory = 'Moderate Risk Cadence';
    categoryColor = 'bg-amber-50 text-amber-900 border-amber-300';
    recommendation = 'Bi-weekly visit cadence (2wk & 4wk) + 6wk checkup.';
  }

  return (
    <div className="bg-slate-900 text-slate-100 p-5 rounded-xl border border-slate-800 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5 text-indigo-400" />
          <h4 className="font-bold text-sm tracking-wide text-white">FOGSI Gestosis Clinical Risk Calculator</h4>
        </div>
        <span className="text-[10px] uppercase font-bold bg-indigo-950 text-indigo-300 px-2.5 py-1 rounded border border-indigo-800">
          OBGYN Decision Support
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
        {criteriaList.map((item) => {
          const active = selectedCriteria.includes(item.id);
          return (
            <button
              type="button"
              key={item.id}
              onClick={() => toggleCriteria(item.id)}
              className={`p-2.5 rounded-lg border transition text-left flex items-center justify-between cursor-pointer ${
                active
                  ? 'bg-indigo-950 border-indigo-500 text-white shadow-xs'
                  : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700 hover:text-slate-200'
              }`}
            >
              <span>{item.label}</span>
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${active ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
                +{item.score} pts
              </span>
            </button>
          );
        })}
      </div>

      {/* Calculated Risk Output Bar */}
      <div className={`p-3.5 rounded-lg border text-xs flex items-center justify-between ${categoryColor}`}>
        <div className="space-y-0.5">
          <div className="font-bold flex items-center space-x-2">
            <span>Score: {totalScore} pts</span>
            <span>—</span>
            <span className="font-extrabold uppercase tracking-wide">{riskCategory}</span>
          </div>
          <p className="text-[11px] opacity-90">{recommendation}</p>
        </div>

        <div className="text-right pl-3">
          <span className="text-[10px] font-mono opacity-75 block">Protocol Auto-Applied</span>
        </div>
      </div>
    </div>
  );
}
