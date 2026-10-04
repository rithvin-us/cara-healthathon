import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import { SESSION_EXPIRED_EVENT, session, systemApi } from '../api/client';

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [user, setUser] = useState(() => session.load());
  const [sessionExpired, setSessionExpired] = useState(false);
  const [health, setHealth] = useState(null);
  // Bumped after anything that changes data shown on several pages (e.g. the
  // daily job), so open pages reload instead of the whole app refreshing.
  const [dataVersion, setDataVersion] = useState(0);

  useEffect(() => {
    const onExpired = () => {
      setUser(null);
      setSessionExpired(true);
    };
    window.addEventListener(SESSION_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(SESSION_EXPIRED_EVENT, onExpired);
  }, []);

  useEffect(() => {
    systemApi
      .health()
      .then((res) => setHealth(res.data))
      .catch(() => setHealth({ status: 'unreachable' }));
  }, []);

  const signIn = useCallback((tokenResponse) => {
    setSessionExpired(false);
    setUser(session.save(tokenResponse));
  }, []);

  const signOut = useCallback(() => {
    session.clear();
    setUser(null);
  }, []);

  const refreshData = useCallback(() => setDataVersion((v) => v + 1), []);

  const value = useMemo(
    () => ({ user, signIn, signOut, sessionExpired, health, dataVersion, refreshData }),
    [user, signIn, signOut, sessionExpired, health, dataVersion, refreshData],
  );

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useApp must be used inside AppProvider');
  return ctx;
}
