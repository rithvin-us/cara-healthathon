import { Link } from 'react-router-dom';
import { PageShell } from '../components/Feedback';

export default function NotFound() {
  return (
    <PageShell>
      <h1 className="text-2xl font-bold">Page not found</h1>
      <p className="text-sm text-ink-soft mt-2">The link may be old, or the page may have moved.</p>
      <Link to="/worklist" className="btn-primary mt-6">
        Go to follow-ups
      </Link>
    </PageShell>
  );
}
