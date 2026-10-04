// Risk factors that change the follow-up cadence (FOGSI guidance). The schedule
// itself comes from the API, so this only collects flags.
export const RISK_CRITERIA = [
  { id: 'hypertension', label: 'High blood pressure or pre-eclampsia', flag: 'hypertension', effect: 'weekly checks' },
  { id: 'hemorrhage_history', label: 'Heavy bleeding after birth (PPH)', flag: 'hemorrhage_history', effect: 'weekly checks' },
  { id: 'anemia', label: 'Severe anaemia (Hb below 8 g/dL)', flag: 'anemia', effect: 'checks at 2 and 4 weeks' },
  { id: 'c_section', label: 'Caesarean delivery', flag: 'c_section', effect: 'checks at 2 and 4 weeks' },
  { id: 'twins', label: 'Twins or more', flag: 'other', effect: 'specialist follow-up' },
  { id: 'diabetes', label: 'Gestational diabetes', flag: 'other', effect: 'specialist follow-up' },
];

export const flagsFor = (criteriaIds) =>
  Array.from(new Set(RISK_CRITERIA.filter((c) => criteriaIds.includes(c.id)).map((c) => c.flag)));
