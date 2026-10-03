import axios from 'axios';

// Same-origin by default: Vite proxies /api in development and Vercel routes
// /api to the Python function in production. Override for a separate API host.
const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

export const SESSION_EXPIRED_EVENT = 'cara:session-expired';
const TOKEN_KEY = 'cara_token';
const USER_KEY = 'cara_user';

export const session = {
  load() {
    try {
      const token = localStorage.getItem(TOKEN_KEY);
      const user = JSON.parse(localStorage.getItem(USER_KEY) || 'null');
      return token && user ? user : null;
    } catch {
      return null;
    }
  },
  save(tokenResponse) {
    const user = {
      user_id: tokenResponse.user_id,
      name: tokenResponse.name,
      role: tokenResponse.role,
      facility_id: tokenResponse.facility_id,
      facility_name: tokenResponse.facility_name,
    };
    localStorage.setItem(TOKEN_KEY, tokenResponse.access_token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
    return user;
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  token: () => localStorage.getItem(TOKEN_KEY),
};

const api = axios.create({ baseURL: API_BASE_URL, timeout: 20000 });

api.interceptors.request.use((config) => {
  const token = session.token();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const isAuthCall = error.config?.url?.startsWith('/auth/');
    if (error.response?.status === 401 && !isAuthCall) {
      session.clear();
      window.dispatchEvent(new Event(SESSION_EXPIRED_EVENT));
    }
    return Promise.reject(error);
  },
);

// One readable sentence for any failed request.
export function errorMessage(error, fallback = 'Something went wrong. Please try again.') {
  if (!error) return fallback;
  if (error.code === 'ECONNABORTED') return 'The server took too long to answer. Please try again.';
  if (!error.response) return "Can't reach the Cara server. Check that the API is running and try again.";
  const detail = error.response.data?.detail;
  if (typeof detail === 'string') return detail;
  return fallback;
}

export const authApi = {
  config: () => api.get('/auth/config'),
  login: (email, password) => api.post('/auth/login', { email, password }),
  quickLogin: (role) => api.post('/auth/quick-login', { role }),
  me: () => api.get('/auth/me'),
};

export const systemApi = {
  health: () => api.get('/health'),
};

export const patientApi = {
  previewSchedule: (deliveryDate, riskFlags) =>
    api.post('/schedule/preview', { delivery_date: deliveryDate, risk_flags: riskFlags }),
  createPatient: (data) => api.post('/patients', data),
  getPatientDetail: (id) => api.get(`/patients/${id}`),
  applyRiskFlag: (id, flagType) => api.post(`/patients/${id}/risk-flags`, { flag_type: flagType }),
  closePlan: (id, reason) => api.post(`/patients/${id}/plan/close`, { reason }),
  auditTrail: (id) => api.get(`/audit-log/patients/${id}`),
};

export const worklistApi = {
  get: (visitType, riskFlag) => {
    const params = {};
    if (visitType) params.visit_type = visitType;
    if (riskFlag) params.risk_flag = riskFlag;
    return api.get('/worklist', { params });
  },
};

export const visitApi = {
  markComplete: (visitId, completedDate, note) =>
    api.post(`/visits/${visitId}/complete`, { completed_date: completedDate, note: note || null }),
  markMissed: (visitId, reason) => api.post(`/visits/${visitId}/missed`, { reason }),
  reschedule: (visitId, dueDate) => api.patch(`/visits/${visitId}/reschedule`, { due_date: dueDate }),
  previewMessage: (visitId) => api.get(`/visits/${visitId}/message-preview`),
  sendReminder: (visitId) => api.post(`/visits/${visitId}/nudge`),
};

export const familyApi = {
  add: (patientId, data) => api.post(`/patients/${patientId}/family-members`, data),
  setConsent: (familyId, consentGiven) =>
    api.patch(`/family-members/${familyId}/consent`, { consent_given: consentGiven }),
};

export const reportApi = {
  getOutcomes: (startDate, endDate) => {
    const params = {};
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return api.get('/reports/outcomes', { params });
  },
  downloadCsv: (startDate, endDate, anonymize) => {
    const params = { export: 'csv', anonymize };
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
    return api.get('/reports/outcomes', { params, responseType: 'blob' });
  },
};

export const adminApi = {
  getStaff: () => api.get('/admin/staff'),
  createStaff: (data) => api.post('/admin/staff', data),
  toggleStaffActive: (userId) => api.patch(`/admin/staff/${userId}/toggle-active`),
  getWeeklyDigest: () => api.get('/admin/digest'),
  runDailyJob: () => api.post('/admin/scheduler/run'),
  resetDemo: () => api.post('/admin/demo/reset'),
};

export default api;
