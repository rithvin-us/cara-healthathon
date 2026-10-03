import { ArrowLeft } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { errorMessage, familyApi, patientApi, visitApi } from '../api/client';
import { ErrorBanner, Loading, PageShell } from '../components/Feedback';
import Modal from '../components/Modal';
import { useToast } from '../components/Toast';
import VisitActionModal from '../components/VisitActionModal';
import WhatsAppPreviewModal from '../components/WhatsAppPreviewModal';
import { useApp } from '../context/AppContext';
import { can } from '../lib/access';
import { formatDate, formatDateTime, formatPhone, todayISO } from '../lib/format';
import { RELATIONS, RISK_LABELS, actionLabel, riskLabel, visitLabel } from '../lib/labels';

const STATUS = {
  completed: { text: 'Done', className: 'text-ok font-semibold', dot: 'bg-ok' },
  missed: { text: 'Missed', className: 'text-ink-soft font-semibold', dot: 'bg-ink-faint' },
  overdue: { text: 'Late', className: 'text-late font-semibold', dot: 'bg-late' },
  due_today: { text: 'Due today', className: 'text-soon font-semibold', dot: 'bg-soon' },
  upcoming: { text: 'Upcoming', className: 'text-ink-soft', dot: 'bg-rule-strong' },
};

const CLOSE_REASONS = ['Follow-up complete', 'Care transferred to another facility', 'Moved away from the area'];

function Section({ title, action, children }) {
  return (
    <section className="border-t border-rule pt-6 mt-8">
      <div className="flex items-center justify-between gap-4">
        <h2 className="text-base font-bold">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

function AddFamilyModal({ patient, onClose, onSaved }) {
  const [form, setForm] = useState({ name: '', relation: 'Husband', contact_number: '', consent_given: true });
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await familyApi.add(patient.patient_id, form);
      onSaved(form.name);
    } catch (err) {
      setError(errorMessage(err, "Couldn't add this family member."));
      setSaving(false);
    }
  };

  return (
    <Modal title="Add family member" subtitle={`They'll get reminders about ${patient.name}'s checkups.`} onClose={onClose}>
      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="fm-name" className="label">
            Name
          </label>
          <input
            id="fm-name"
            required
            minLength={2}
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="field"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="fm-relation" className="label">
              Relation
            </label>
            <select
              id="fm-relation"
              value={form.relation}
              onChange={(e) => setForm({ ...form, relation: e.target.value })}
              className="field"
            >
              {RELATIONS.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="fm-phone" className="label">
              Mobile
            </label>
            <input
              id="fm-phone"
              type="tel"
              required
              value={form.contact_number}
              onChange={(e) => setForm({ ...form, contact_number: e.target.value })}
              placeholder="98765 43211"
              className="field"
            />
          </div>
        </div>
        <label className="flex items-start gap-2 text-sm cursor-pointer">
          <input
            type="checkbox"
            checked={form.consent_given}
            onChange={(e) => setForm({ ...form, consent_given: e.target.checked })}
            className="h-4 w-4 mt-0.5 accent-[#0E5A54]"
          />
          <span>{patient.name} agreed, verbally or in writing, that this person may get WhatsApp reminders.</span>
        </label>
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Adding…' : 'Add family member'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

function SimpleFormModal({ title, subtitle, submitLabel, onClose, onSubmit, children }) {
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const handle = async (e) => {
    e.preventDefault();
    setSaving(true);
    setError('');
    try {
      await onSubmit(new FormData(e.currentTarget));
    } catch (err) {
      setError(errorMessage(err));
      setSaving(false);
    }
  };
  return (
    <Modal title={title} subtitle={subtitle} onClose={onClose}>
      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} />
        </div>
      )}
      <form onSubmit={handle} className="space-y-4">
        {children}
        <div className="flex justify-end gap-3 pt-2">
          <button type="button" onClick={onClose} className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={saving}>
            {saving ? 'Saving…' : submitLabel}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export default function PatientDetail() {
  const { id } = useParams();
  const { user, dataVersion } = useApp();
  const toast = useToast();
  const [data, setData] = useState(null);
  const [trail, setTrail] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null); // { kind, visit? }
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    setError('');
    try {
      const [detail, audit] = await Promise.all([patientApi.getPatientDetail(id), patientApi.auditTrail(id)]);
      setData(detail.data);
      setTrail(audit.data);
    } catch (err) {
      setError(
        err.response?.status === 404
          ? "We couldn't find this mother at your hospital."
          : errorMessage(err, "Couldn't load her record."),
      );
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    load();
  }, [load, dataVersion]);

  const close = () => setModal(null);
  const savedAnd = (message) => {
    toast.success(message);
    setModal(null);
    load();
  };

  const sendReminder = async (visit) => {
    setBusyId(visit.visit_id);
    try {
      const res = await visitApi.sendReminder(visit.visit_id);
      const failed = res.data.filter((n) => n.status === 'failed').length;
      if (failed) toast.error(`${failed} of ${res.data.length} reminders failed.`);
      else toast.success(`Reminder sent to ${res.data.length} ${res.data.length === 1 ? 'number' : 'numbers'}.`);
      load();
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't send the reminder."));
    } finally {
      setBusyId(null);
    }
  };

  const toggleConsent = async (member) => {
    setBusyId(`fm-${member.family_id}`);
    try {
      await familyApi.setConsent(member.family_id, !member.latest_consent);
      toast.success(
        member.latest_consent
          ? `${member.name} will get no more reminders.`
          : `${member.name} will get reminders again.`,
      );
      load();
    } catch (err) {
      toast.error(errorMessage(err, "Couldn't update consent."));
    } finally {
      setBusyId(null);
    }
  };

  if (loading) {
    return (
      <PageShell>
        <Loading />
      </PageShell>
    );
  }

  if (!data) {
    return (
      <PageShell>
        <ErrorBanner message={error} onRetry={load} />
        <Link to="/worklist" className="btn-link inline-block mt-4">
          Back to follow-ups
        </Link>
      </PageShell>
    );
  }

  const { patient, newborns, active_plan: plan, family_members: family, nudges } = data;
  const planOpen = plan?.status === 'active';
  const existingFlags = new Set(plan?.risk_flags.map((rf) => rf.flag_type) || []);
  const baby = newborns[0];

  return (
    <PageShell>
      <Link to="/worklist" className="inline-flex items-center btn-link mb-4">
        <ArrowLeft className="h-4 w-4 mr-1" aria-hidden="true" />
        Back to follow-ups
      </Link>

      {error && (
        <div className="mb-4">
          <ErrorBanner message={error} onRetry={load} />
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-bold">{patient.name}</h1>
        {plan && !planOpen && (
          <span className="text-xs font-semibold bg-paper border border-rule-strong rounded px-2 py-0.5">
            Plan closed: {plan.closed_reason}
          </span>
        )}
      </div>
      <p className="text-sm text-ink-soft mt-1">
        Delivered {formatDate(patient.delivery_date)}, discharged {formatDate(patient.discharge_date)}.{' '}
        {formatPhone(patient.contact_number)} · speaks {patient.preferred_language}.
        {baby && ` Baby: ${baby.name_or_initial || 'not named yet'}${baby.gender ? ` (${baby.gender.toLowerCase()})` : ''}.`}
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-x-10">
        <div className="lg:col-span-2">
          <Section title="Checkup schedule">
            {!plan || plan.visits.length === 0 ? (
              <p className="text-sm text-ink-soft mt-3">No checkups are scheduled.</p>
            ) : (
              <ol className="mt-4 border-l-2 border-rule">
                {plan.visits.map((v) => {
                  const s = STATUS[v.status] || STATUS.upcoming;
                  const open = planOpen && !['completed', 'missed'].includes(v.status);
                  return (
                    <li key={v.visit_id} className="relative pl-5 py-3 border-b border-rule last:border-0">
                      <span className={`absolute -left-[5px] top-5 h-2 w-2 rounded-full ${s.dot}`} aria-hidden="true" />
                      <div className="flex flex-wrap items-start justify-between gap-x-4 gap-y-2">
                        <div className="text-sm">
                          <div className="font-semibold">{visitLabel(v.visit_type)}</div>
                          <div className="text-[13px] text-ink-soft mt-0.5">
                            {v.status === 'completed' ? (
                              <>
                                <span className={s.className}>{s.text}</span> on {formatDate(v.completed_date)}
                              </>
                            ) : (
                              <>
                                Due {formatDate(v.due_date)} · <span className={s.className}>{s.text}</span>
                              </>
                            )}
                          </div>
                          {v.note && <div className="text-[13px] text-ink-soft mt-1">{v.note}</div>}
                        </div>
                        {open && (
                          <div className="flex items-center gap-4 text-sm">
                            {can(user, 'reschedule') && (
                              <button type="button" className="btn-link" onClick={() => setModal({ kind: 'reschedule', visit: v })}>
                                Reschedule
                              </button>
                            )}
                            {v.status !== 'upcoming' && (
                              <>
                                <button
                                  type="button"
                                  className="btn-link"
                                  onClick={() => setModal({ kind: 'preview', visit: v })}
                                >
                                  Preview
                                </button>
                                <button
                                  type="button"
                                  className="btn-link"
                                  disabled={busyId === v.visit_id}
                                  onClick={() => sendReminder(v)}
                                >
                                  {busyId === v.visit_id ? 'Sending…' : 'Send reminder'}
                                </button>
                              </>
                            )}
                            <button
                              type="button"
                              className={v.status === 'upcoming' ? 'btn-link' : 'btn-primary py-1.5 px-3'}
                              onClick={() => setModal({ kind: 'record', visit: v })}
                            >
                              Record visit
                            </button>
                          </div>
                        )}
                      </div>
                    </li>
                  );
                })}
              </ol>
            )}
          </Section>

          <Section title="Reminders sent">
            {nudges.length === 0 ? (
              <p className="text-sm text-ink-soft mt-3">
                No reminders yet. Cara sends one on the day a checkup is due and one if it becomes late.
              </p>
            ) : (
              <ul className="mt-3">
                {nudges.slice(0, 8).map((n) => (
                  <li key={n.nudge_id} className="py-3 border-b border-rule last:border-0 text-sm">
                    <div className="flex flex-wrap justify-between gap-2">
                      <span className="font-semibold">
                        {n.recipient_type === 'mother' ? patient.name : family.find((f) => f.contact_number === n.recipient_contact)?.name || 'Family'}{' '}
                        <span className="font-normal text-ink-soft">
                          via {n.channel === 'sms' ? 'SMS' : 'WhatsApp'} · {n.trigger === 'manual' ? 'sent by staff' : n.trigger === 'overdue' ? 'late reminder' : 'due-day reminder'}
                        </span>
                      </span>
                      <span className={n.status === 'failed' ? 'text-late font-semibold' : 'text-ink-faint'}>
                        {n.status === 'failed' ? 'Failed' : n.status.charAt(0).toUpperCase() + n.status.slice(1)} ·{' '}
                        {formatDateTime(n.sent_at)}
                      </span>
                    </div>
                    <p className="text-[13px] text-ink-soft mt-1 line-clamp-2">{n.message_text}</p>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          <Section title="Activity">
            <p className="text-xs text-ink-faint mt-1">Every change to her plan, visits and consent. This log can't be edited.</p>
            <ul className="mt-3 text-sm">
              {trail.slice(0, 12).map((e) => (
                <li key={e.audit_id} className="py-2 border-b border-rule last:border-0 flex flex-wrap justify-between gap-2">
                  <span>
                    <span className="font-semibold">{actionLabel(e.action)}</span>
                    <span className="text-ink-soft"> · {e.details}</span>
                  </span>
                  <span className="text-ink-faint text-[13px]">
                    {e.actor_name} · {formatDateTime(e.timestamp)}
                  </span>
                </li>
              ))}
            </ul>
          </Section>
        </div>

        <div>
          <Section
            title="Risk flags"
            action={
              planOpen &&
              can(user, 'riskFlags') &&
              existingFlags.size < Object.keys(RISK_LABELS).length && (
                <button type="button" className="btn-link" onClick={() => setModal({ kind: 'risk' })}>
                  Add risk flag
                </button>
              )
            }
          >
            {plan?.risk_flags.length ? (
              <>
                <p className="text-sm text-late font-semibold mt-3">{plan.risk_flags.map((rf) => riskLabel(rf.flag_type)).join(', ')}</p>
                <p className="text-xs text-ink-faint mt-1">Extra checkups are on her schedule for these.</p>
              </>
            ) : (
              <p className="text-sm text-ink-soft mt-3">None. She follows the standard WHO schedule.</p>
            )}
          </Section>

          <Section
            title="Family contacts"
            action={
              planOpen && (
                <button type="button" className="btn-link" onClick={() => setModal({ kind: 'family' })}>
                  Add
                </button>
              )
            }
          >
            {family.length === 0 ? (
              <p className="text-sm text-ink-soft mt-3">None added. Add a relative if she'd like them reminded too.</p>
            ) : (
              <ul className="mt-3">
                {family.map((fm) => (
                  <li key={fm.family_id} className="py-3 border-b border-rule last:border-0 text-sm">
                    <div className="font-semibold">
                      {fm.name}, <span className="font-normal">{fm.relation.toLowerCase()}</span>
                    </div>
                    <div className="text-[13px] text-ink-soft mt-0.5">{formatPhone(fm.contact_number)}</div>
                    <div className="flex items-center justify-between gap-2 mt-1">
                      {fm.latest_consent ? (
                        <span className="text-[13px] text-ok font-semibold">Gets reminders</span>
                      ) : (
                        <span className="text-[13px] text-late font-semibold">Consent withdrawn</span>
                      )}
                      <button
                        type="button"
                        disabled={busyId === `fm-${fm.family_id}`}
                        onClick={() => toggleConsent(fm)}
                        className={fm.latest_consent ? 'btn-danger-link' : 'btn-link'}
                      >
                        {fm.latest_consent ? 'Withdraw consent' : 'Record consent'}
                      </button>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </Section>

          {planOpen && (
            <Section title="Discharge plan">
              <p className="text-sm text-ink-soft mt-3">
                Close the plan when follow-up is finished or her care moves elsewhere. She'll leave the follow-up list.
              </p>
              <button type="button" className="btn-secondary mt-3" onClick={() => setModal({ kind: 'close' })}>
                Close plan
              </button>
            </Section>
          )}
        </div>
      </div>

      {modal?.kind === 'record' && (
        <VisitActionModal
          visit={modal.visit}
          patientName={patient.name}
          onClose={close}
          onSaved={(outcome) => savedAnd(`${visitLabel(modal.visit.visit_type)} recorded as ${outcome === 'completed' ? 'done' : 'missed'}.`)}
        />
      )}
      {modal?.kind === 'preview' && (
        <WhatsAppPreviewModal visitId={modal.visit.visit_id} onClose={close} onSend={() => sendReminder(modal.visit)} />
      )}
      {modal?.kind === 'family' && (
        <AddFamilyModal patient={patient} onClose={close} onSaved={(name) => savedAnd(`${name} added.`)} />
      )}
      {modal?.kind === 'reschedule' && (
        <SimpleFormModal
          title="Reschedule checkup"
          subtitle={`${visitLabel(modal.visit.visit_type)}, now due ${formatDate(modal.visit.due_date)}`}
          submitLabel="Save new date"
          onClose={close}
          onSubmit={async (fd) => {
            await visitApi.reschedule(modal.visit.visit_id, fd.get('due_date'));
            savedAnd(`Moved to ${formatDate(fd.get('due_date'))}.`);
          }}
        >
          <div>
            <label htmlFor="new-date" className="label">
              New date
            </label>
            <input id="new-date" name="due_date" type="date" required min={patient.delivery_date} defaultValue={todayISO()} className="field" />
          </div>
        </SimpleFormModal>
      )}
      {modal?.kind === 'risk' && (
        <SimpleFormModal
          title="Add risk flag"
          subtitle="Extra checkups are added. Existing visits and history stay as they are."
          submitLabel="Add flag"
          onClose={close}
          onSubmit={async (fd) => {
            const res = await patientApi.applyRiskFlag(patient.patient_id, fd.get('flag'));
            const added = res.data.visits.length - plan.visits.length;
            savedAnd(`${riskLabel(fd.get('flag'))} added${added > 0 ? `, with ${added} extra checkups` : ''}.`);
          }}
        >
          <div>
            <label htmlFor="flag" className="label">
              Risk
            </label>
            <select id="flag" name="flag" className="field">
              {Object.entries(RISK_LABELS)
                .filter(([value]) => !existingFlags.has(value))
                .map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
            </select>
          </div>
        </SimpleFormModal>
      )}
      {modal?.kind === 'close' && (
        <SimpleFormModal
          title="Close discharge plan"
          subtitle="Open checkups stop getting reminders. This is recorded in her activity log."
          submitLabel="Close plan"
          onClose={close}
          onSubmit={async (fd) => {
            await patientApi.closePlan(patient.patient_id, fd.get('reason'));
            savedAnd(`${patient.name}'s plan is closed.`);
          }}
        >
          <div>
            <label htmlFor="reason" className="label">
              Reason
            </label>
            <select id="reason" name="reason" className="field">
              {CLOSE_REASONS.map((r) => (
                <option key={r}>{r}</option>
              ))}
            </select>
          </div>
        </SimpleFormModal>
      )}
    </PageShell>
  );
}
