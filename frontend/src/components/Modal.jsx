import { useEffect, useId, useRef } from 'react';

export default function Modal({ title, subtitle, onClose, children, size = 'md' }) {
  const titleId = useId();
  const panelRef = useRef(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;

  // Runs once per open: focus the first field, close on Escape, lock page scroll.
  useEffect(() => {
    const previouslyFocused = document.activeElement;
    const focusable = panelRef.current?.querySelector('input, select, textarea, button:not([data-close])');
    focusable?.focus();

    const onKey = (e) => {
      if (e.key === 'Escape') onCloseRef.current();
    };
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
      previouslyFocused?.focus?.();
    };
  }, []);

  const width = size === 'sm' ? 'max-w-sm' : 'max-w-md';

  return (
    <div
      className="fixed inset-0 bg-ink/40 flex items-center justify-center p-4 z-50"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className={`bg-white rounded-md shadow-lg w-full ${width} p-6 max-h-[90vh] overflow-y-auto`}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id={titleId} className="text-base font-bold text-ink">
              {title}
            </h2>
            {subtitle && <p className="text-sm text-ink-soft mt-1">{subtitle}</p>}
          </div>
          <button
            type="button"
            data-close
            onClick={onClose}
            className="text-ink-faint hover:text-ink text-xl leading-none -mt-1"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="mt-4">{children}</div>
      </div>
    </div>
  );
}
