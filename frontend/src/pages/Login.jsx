import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { authApi, errorMessage } from '../api/client';
import { ErrorBanner } from '../components/Feedback';
import { useApp } from '../context/AppContext';

const ROLE_COPY = {
  Doctor: { title: 'Doctor', does: 'Plan discharges and set risk flags' },
  Coordinator: { title: 'Nurse coordinator', does: 'Call mothers who are due or late' },
  Admin: { title: 'Hospital admin', does: 'See outcomes and manage staff' },
};

export default function Login() {
  const { signIn, sessionExpired } = useApp();
  const navigate = useNavigate();
  const location = useLocation();
  const [config, setConfig] = useState(null);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  useEffect(() => {
    authApi
      .config()
      .then((res) => setConfig(res.data))
      .catch((err) => {
        setConfig({ demo_mode: false, demo_accounts: [] });
        setError(errorMessage(err));
      });
  }, []);

  const finish = (data) => {
    signIn(data);
    navigate(location.state?.from || '/worklist', { replace: true });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy('form');
    try {
      const res = await authApi.login(email.trim(), password);
      finish(res.data);
    } catch (err) {
      setError(errorMessage(err, "Couldn't sign in. Try again."));
      setBusy('');
    }
  };

  const handleDemo = async (role) => {
    setError('');
    setBusy(role);
    try {
      const res = await authApi.quickLogin(role);
      finish(res.data);
    } catch (err) {
      setError(errorMessage(err, "Couldn't sign in to the demo account."));
      setBusy('');
    }
  };

  const facilityName = config?.facility_name || 'your hospital';

  return (
    <div className="min-h-screen bg-paper text-ink lg:flex">
      <div className="lg:w-1/2 lg:h-screen lg:sticky lg:top-0 relative">
        <img
          src="/images/mother-at-home.jpg"
          alt="A mother in a saree holds her baby at the door of their home"
          width="1600"
          height="1067"
          loading="eager"
          decoding="async"
          className="block h-60 sm:h-80 w-full object-cover object-[center_30%] lg:h-full lg:object-[52%_center]"
        />
        <p className="absolute bottom-2 right-3 text-[11px] text-white/85 drop-shadow">
          Photo:{' '}
          <a
            href="https://www.pexels.com/photo/mother-holding-child-in-traditional-indian-clothing-37019500/"
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            Juber Ahmed Sahel, Pexels
          </a>
        </p>
      </div>

      <div className="lg:w-1/2 lg:min-h-screen flex items-center py-10 px-4 sm:px-6 lg:px-12">
        <div className="w-full max-w-md mx-auto">
          <div className="flex items-center gap-2">
            <img src="/favicon.svg" alt="" className="h-7 w-7" />
            <span className="text-scrub font-bold text-xl">Cara</span>
          </div>
          <h1 className="text-3xl font-bold leading-tight mt-6">Postnatal follow-up for {facilityName}</h1>
          <p className="text-sm text-ink-soft mt-4">
            Every mother discharged here is due checkups at 24 hours, 3 days, 10 days and 6 weeks. Cara tracks who is
            due or late, and reminds her and her family on WhatsApp in her own language.
          </p>

          {sessionExpired && (
            <div className="mt-6 border-l-4 border-soon bg-soon-tint text-soon text-sm px-3 py-2" role="status">
              Your session ended. Please sign in again.
            </div>
          )}
          {error && (
            <div className="mt-6">
              <ErrorBanner message={error} />
            </div>
          )}

          <form onSubmit={handleSubmit} className="card mt-6 p-5 space-y-4">
            <h2 className="text-base font-bold">Staff sign-in</h2>
            <div>
              <label htmlFor="email" className="label">
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="field"
              />
            </div>
            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="field"
              />
            </div>
            <button type="submit" className="btn-primary w-full" disabled={!!busy}>
              {busy === 'form' ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          {config?.demo_mode && config.demo_accounts.length > 0 && (
            <div className="card mt-6">
              <div className="px-5 py-4">
                <h2 className="text-base font-bold">Or try a demo account</h2>
                <p className="text-sm text-ink-soft mt-1">One click, no password. Every patient here is made up.</p>
              </div>
              {config.demo_accounts.map((acct) => (
                <button
                  key={acct.role}
                  type="button"
                  onClick={() => handleDemo(acct.role)}
                  disabled={!!busy}
                  className="w-full px-5 py-4 border-t border-rule text-left flex items-center justify-between gap-4 hover:bg-paper disabled:cursor-default last:rounded-b-md"
                >
                  <div>
                    <div className="text-sm font-semibold">{ROLE_COPY[acct.role]?.title || acct.role}</div>
                    <div className="text-xs text-ink-faint">{acct.name}</div>
                    <div className="text-sm text-ink-soft mt-1">{ROLE_COPY[acct.role]?.does}</div>
                  </div>
                  <span className="text-sm text-scrub font-semibold shrink-0">
                    {busy === acct.role ? 'Signing in…' : 'Sign in'}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
