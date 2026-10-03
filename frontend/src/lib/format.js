const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// API dates are plain calendar dates ("2026-10-03"). Parse them as local dates;
// `new Date("2026-10-03")` would read them as UTC midnight and can shift a day.
export function parseDate(value) {
  if (!value) return null;
  const [y, m, d] = String(value).slice(0, 10).split('-').map(Number);
  return new Date(y, m - 1, d);
}

export function formatDate(value) {
  const d = parseDate(value);
  return d ? `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}` : '';
}

export function formatShortDate(value) {
  const d = parseDate(value);
  return d ? `${d.getDate()} ${MONTHS[d.getMonth()]}` : '';
}

// API timestamps are naive UTC.
export function parseTimestamp(value) {
  if (!value) return null;
  const s = String(value);
  return new Date(/[zZ]|[+-]\d\d:\d\d$/.test(s) ? s : `${s}Z`);
}

export function formatDateTime(value) {
  const d = parseTimestamp(value);
  if (!d) return '';
  const time = d.toLocaleTimeString('en-IN', { hour: 'numeric', minute: '2-digit' });
  return `${d.getDate()} ${MONTHS[d.getMonth()]}, ${time}`;
}

export function timeAgo(value) {
  const d = parseTimestamp(value);
  if (!d) return '';
  const minutes = Math.round((Date.now() - d.getTime()) / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;
  const days = Math.round(hours / 24);
  return days === 1 ? 'yesterday' : `${days} days ago`;
}

export function toISODate(date) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export const todayISO = () => toISODate(new Date());

export function daysBetween(fromISO, toISO) {
  const a = parseDate(fromISO);
  const b = parseDate(toISO);
  return Math.round((b - a) / 86400000);
}

export function formatPhone(value) {
  const s = String(value || '');
  const m = s.match(/^\+91(\d{5})(\d{5})$/);
  // Non-breaking spaces keep the number on one line.
  return m ? `+91\u00a0${m[1]}\u00a0${m[2]}` : s;
}
