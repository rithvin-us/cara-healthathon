// Which roles see which screens and actions. The API enforces the same rules.
export const ROLE_ACCESS = {
  newDischarge: ['Doctor', 'Admin'],
  reports: ['Doctor', 'Admin'],
  staff: ['Admin'],
  riskFlags: ['Doctor'],
  reschedule: ['Doctor', 'Coordinator'],
};

export const can = (user, capability) => !!user && ROLE_ACCESS[capability].includes(user.role);
