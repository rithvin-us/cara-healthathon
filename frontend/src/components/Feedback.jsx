export function ErrorBanner({ message, onRetry }) {
  if (!message) return null;
  return (
    <div className="border-l-4 border-late bg-late-tint text-late text-sm px-3 py-2 flex items-center justify-between gap-4" role="alert">
      <span>{message}</span>
      {onRetry && (
        <button type="button" onClick={onRetry} className="font-semibold underline underline-offset-2 shrink-0">
          Try again
        </button>
      )}
    </div>
  );
}

export function Loading({ label = 'Loading…' }) {
  return (
    <p className="text-sm text-ink-soft py-8" role="status">
      {label}
    </p>
  );
}

export function PageShell({ children }) {
  return <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 text-ink">{children}</div>;
}
