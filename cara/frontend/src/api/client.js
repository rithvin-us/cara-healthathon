import axios from 'axios';

const API_BASE_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.PROD ? '/api/v1' : 'http://localhost:8000/api/v1');

const api = axios.create({
  baseURL: API_BASE_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('cara_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const authApi = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  quickLogin: (role) => api.post('/auth/quick-login', { role }),
};


export const patientApi = {
  createPatient: (data) => api.post('/patients', data),
  getPatientDetail: (id) => api.get(`/patients/${id}`),
  applyRiskFlag: (id, flagType) => api.post(`/patients/${id}/risk-flags`, { flag_type: flagType }),
};

export const worklistApi = {
  getRankedWorklist: (visitType, riskFlag) => {
    const params = {};
    if (visitType) params.visit_type = visitType;
    if (riskFlag) params.risk_flag = riskFlag;
    return api.get('/worklist', { params });
  },
};

export const visitApi = {
  markComplete: (visitId, completedDate, note) =>
    api.post(`/visits/${visitId}/complete`, { completed_date: completedDate, note }),
  markMissed: (visitId, reason) =>
    api.post(`/visits/${visitId}/missed`, { reason }),
  manualNudge: (visitId) => api.post(`/visits/${visitId}/nudge`),
};

export const familyApi = {
  addFamilyMember: (patientId, data) => api.post(`/patients/${patientId}/family-members`, data),
  updateConsent: (familyId, consentGiven) => api.patch(`/family-members/${familyId}/consent`, { consent_given: consentGiven }),
};

export const reportApi = {
  getOutcomes: (startDate, endDate) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return api.get('/reports/outcomes', { params });
  },
  downloadCsv: (startDate, endDate, anonymize = false) => {
    const params = { export: 'csv' };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    if (anonymize) params.anonymize = true;
    return api.get('/reports/outcomes', { params, responseType: 'blob' });
  },
};

export const adminApi = {
  getStaff: () => api.get('/admin/staff'),
  createStaff: (data) => api.post('/admin/staff', data),
  toggleStaffActive: (userId) => api.patch(`/admin/staff/${userId}/toggle-active`),
  getWeeklyDigest: () => api.get('/admin/digest'),
  triggerScheduler: (simulateDate) => api.post('/admin/scheduler/run', null, { params: simulateDate ? { simulate_date: simulateDate } : {} }),
};

export default api;
