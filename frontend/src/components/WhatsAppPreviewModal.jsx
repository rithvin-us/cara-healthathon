import { useEffect, useState } from 'react';
import { errorMessage, visitApi } from '../api/client';
import { formatPhone } from '../lib/format';
import { REMINDER_LANGUAGES } from '../lib/labels';
import { ErrorBanner, Loading } from './Feedback';
import Modal from './Modal';

// Shows the exact text the API would send for this visit right now.
export default function WhatsAppPreviewModal({ visitId, onClose, onSend }) {
  const [preview, setPreview] = useState(null);
  const [error, setError] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    let cancelled = false;
    visitApi
      .previewMessage(visitId)
      .then((res) => !cancelled && setPreview(res.data))
      .catch((err) => !cancelled && setError(errorMessage(err, "Couldn't load the message preview.")));
    return () => {
      cancelled = true;
    };
  }, [visitId]);

  const handleSend = async () => {
    setSending(true);
    try {
      await onSend();
      onClose();
    } finally {
      setSending(false);
    }
  };

  const fallsBackToEnglish = preview && !REMINDER_LANGUAGES.includes(preview.language);

  return (
    <Modal
      title="WhatsApp preview"
      subtitle={preview ? `What ${preview.recipient_name} receives at ${formatPhone(preview.recipient_contact)}` : null}
      onClose={onClose}
      size="sm"
    >
      {error && <ErrorBanner message={error} />}
      {!preview && !error && <Loading />}
      {preview && (
        <>
          <div className="bg-[#EFEAE2] rounded-md p-4">
            <div className="flex justify-end">
              <div className="bg-[#D9FDD3] rounded-md px-3 py-2 max-w-[90%] text-sm text-ink shadow-sm">
                <p className="whitespace-pre-line leading-relaxed">{preview.message_text}</p>
                <div className="text-right text-[11px] text-ink-faint mt-1">✓✓</div>
              </div>
            </div>
          </div>
          <p className="text-xs text-ink-faint mt-3">
            {fallsBackToEnglish
              ? `Sent in English: there's no reviewed ${preview.language} template yet.`
              : `Sent in ${preview.language}, her preferred language.`}{' '}
            Consented family members get a similar message.
            {preview.provider === 'simulated' && ' Demo mode: nothing reaches a real phone.'}
          </p>
        </>
      )}
      <div className="flex justify-end gap-3 mt-6">
        <button type="button" onClick={onClose} className="btn-secondary">
          Close
        </button>
        {onSend && (
          <button type="button" onClick={handleSend} className="btn-primary" disabled={!preview || sending}>
            {sending ? 'Sending…' : 'Send reminder now'}
          </button>
        )}
      </div>
    </Modal>
  );
}
