// Plain-language names for the visit types the backend schedules.
const VISIT_LABELS = {
  '24h Checkup': '24-hour checkup',
  '48-72h Checkup': '3-day checkup',
  '7-14d Checkup': '10-day checkup',
  '6wk Checkup': '6-week checkup',
  'Weekly Risk Checkup (Week 1)': 'Week 1 risk check',
  'Weekly Risk Checkup (Week 2)': 'Week 2 risk check',
  'Weekly Risk Checkup (Week 3)': 'Week 3 risk check',
  'Weekly Risk Checkup (Week 4)': 'Week 4 risk check',
  'Post-op/Anemia Checkup (Week 2)': 'Week 2 wound and anaemia check',
  'Post-op/Anemia Checkup (Week 4)': 'Week 4 wound and anaemia check',
};

export const visitLabel = (type) => VISIT_LABELS[type] || type;
