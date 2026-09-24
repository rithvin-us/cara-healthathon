import React, { useState } from 'react';

export default function FOGSIRiskCalculator({ onSelectRiskFlags }) {
  const [selectedCriteria, setSelectedCriteria] = useState([]);

  const criteriaList = [
    { id: 'hypertension', label: 'High blood pressure or pre-eclampsia', score: 3, riskFlag: 'hypertension' },
    { id: 'hemorrhage_history', label: 'History of heavy bleeding (PPH)', score: 3, riskFlag: 'hemorrhage_history' },
    { id: 'anemia', label: 'Severe anaemia (Hb below 8 g/dL)', score: 2, riskFlag: 'anemia' },
    { id: 'c_section', label: 'Emergency C-section', score: 2, riskFlag: 'c_section' },
    { id: 'twins', label: 'Twins or triplets', score: 2, riskFlag: 'other' },
    { id: 'diabetes', label: 'Gestational diabetes', score: 1, riskFlag: 'other' },
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

  let riskCategory = 'Low risk';
  let categoryColor = 'text-ok';
  let recommendation = 'She gets the standard four checkups.';

  if (totalScore >= 3) {
    riskCategory = 'High risk';
    categoryColor = 'text-late';
    recommendation = 'She gets a weekly check for 4 weeks, then the 6-week checkup.';
  } else if (totalScore >= 1) {
    riskCategory = 'Moderate risk';
    categoryColor = 'text-soon';
    recommendation = 'She gets checks at 2 and 4 weeks, then the 6-week checkup.';
  }

  return (
    <div className="bg-white border border-rule rounded-md p-4">
      <h3 className="text-sm font-bold text-ink">FOGSI risk check</h3>
      <p className="text-xs text-ink-faint mt-1">Tick everything that applies to her.</p>

      <div className="mt-3 space-y-2">
        {criteriaList.map((item) => {
          const active = selectedCriteria.includes(item.id);
          return (
            <label key={item.id} className="flex items-start gap-2 text-sm text-ink cursor-pointer">
              <input
                type="checkbox"
                checked={active}
                onChange={() => toggleCriteria(item.id)}
                className="mt-0.5 h-4 w-4 accent-[#0E5A54]"
              />
              <span>
                {item.label} <span className="text-xs text-ink-faint">({item.score} points)</span>
              </span>
            </label>
          );
        })}
      </div>

      <div className="border-t border-rule pt-3 mt-4 text-sm">
        <p className={`font-semibold ${categoryColor}`}>
          {riskCategory}, {totalScore} {totalScore === 1 ? 'point' : 'points'}.
        </p>
        <p className="text-ink-soft mt-1">{recommendation}</p>
      </div>
    </div>
  );
}
