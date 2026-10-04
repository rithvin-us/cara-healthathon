// Plain-language names for the codes the API uses.

const VISIT_LABELS = {
  '24h Checkup': '24-hour checkup',
  '48-72h Checkup': '3-day checkup',
  '7-14d Checkup': '10-day checkup',
  '6wk Checkup': '6-week checkup',
  'Weekly Risk Checkup (Week 1)': 'Week 1 high-risk check',
  'Weekly Risk Checkup (Week 2)': 'Week 2 high-risk check',
  'Weekly Risk Checkup (Week 3)': 'Week 3 high-risk check',
  'Weekly Risk Checkup (Week 4)': 'Week 4 high-risk check',
  'Post-op/Anemia Checkup (Week 2)': 'Week 2 recovery check',
  'Post-op/Anemia Checkup (Week 4)': 'Week 4 recovery check',
  'Specialist Follow-Up': 'Specialist follow-up',
};

export const visitLabel = (type) => VISIT_LABELS[type] || type;

export const DEFAULT_VISIT_TYPES = ['24h Checkup', '48-72h Checkup', '7-14d Checkup', '6wk Checkup'];

export const RISK_LABELS = {
  hypertension: 'High blood pressure',
  hemorrhage_history: 'PPH history',
  anemia: 'Severe anaemia',
  c_section: 'C-section',
  other: 'Other risk',
};

export const riskLabel = (flag) => RISK_LABELS[flag] || flag;

export const RISK_TIERS = {
  standard: { label: 'Standard schedule', tone: 'text-ok' },
  moderate: { label: 'Moderate risk', tone: 'text-soon' },
  high: { label: 'High risk', tone: 'text-late' },
  specialist: { label: 'Needs specialist follow-up', tone: 'text-soon' },
};

export const LANGUAGES = ['English', 'Hindi', 'Tamil', 'Marathi', 'Gujarati', 'Bengali', 'Telugu', 'Kannada'];

// Reminder templates that have been reviewed; other languages get English.
export const REMINDER_LANGUAGES = ['English', 'Hindi', 'Tamil'];

export const MISSED_REASONS = [
  { value: 'unreachable', label: "Couldn't reach her" },
  { value: 'declined', label: 'She declined the visit' },
  { value: 'moved', label: 'She moved away' },
];

export const RELATIONS = ['Husband', 'Mother', 'Mother-in-law', 'Sister', 'Father', 'Brother', 'Other'];

export const ACTION_LABELS = {
  CREATE_DISCHARGE_PLAN: 'Discharge plan created',
  APPLY_RISK_FLAG: 'Risk flag added',
  MARK_VISIT_COMPLETE: 'Visit marked done',
  MARK_VISIT_MISSED: 'Visit marked missed',
  RESCHEDULE_VISIT: 'Visit rescheduled',
  ADD_FAMILY_CONSENT: 'Family member added',
  GRANT_CONSENT: 'Consent recorded',
  REVOKE_CONSENT: 'Consent withdrawn',
  TRIGGER_NUDGE: 'Reminder sent',
  CLOSE_DISCHARGE_PLAN: 'Plan closed',
  RECOMPUTE_VISIT_STATUSES: 'Statuses updated',
};

export const actionLabel = (action) => ACTION_LABELS[action] || action;
