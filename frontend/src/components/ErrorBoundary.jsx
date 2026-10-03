import { Component } from 'react';

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error('Cara UI error', error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="max-w-xl mx-auto px-4 py-16">
        <h1 className="text-2xl font-bold text-ink">This page hit a problem</h1>
        <p className="text-sm text-ink-soft mt-2">
          Nothing was lost. Reload the page, or go back to the follow-up list.
        </p>
        <div className="mt-6 flex gap-3">
          <button type="button" className="btn-primary" onClick={() => window.location.reload()}>
            Reload
          </button>
          <a className="btn-secondary" href="/worklist">
            Follow-ups
          </a>
        </div>
      </div>
    );
  }
}
