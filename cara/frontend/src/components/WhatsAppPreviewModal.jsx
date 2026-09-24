import React from 'react';

export default function WhatsAppPreviewModal({ isOpen, onClose, patientName, recipientContact, visitType, dueDate, facilityName, language }) {
  if (!isOpen) return null;

  const sampleMessages = [
    {
      sender: 'system',
      text: `Namaste ${patientName}! This is a reminder from ${facilityName} for your upcoming postnatal checkup (${visitType}) scheduled on ${dueDate}. Please visit the clinic or call us if you need to reschedule.`,
      time: '10:05 AM',
      status: 'delivered',
    },
    {
      sender: 'system',
      text: `Important: Please bring your hospital discharge card and baby's immunization chart for the checkup. Reply 1 to confirm, or 2 to request a callback.`,
      time: '10:06 AM',
      status: 'delivered',
    }
  ];

  return (
    <div className="fixed inset-0 bg-ink/40 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-md shadow-lg max-w-sm w-full p-6">
        <h2 className="text-base font-bold text-ink">Message preview</h2>
        <p className="text-[13px] text-ink-soft mt-1">
          What {patientName} will receive on WhatsApp at {recipientContact}
        </p>

        <div className="bg-[#EFEAE2] rounded-md p-4 mt-4 max-h-80 overflow-y-auto">
          <div className="flex justify-end">
            <div className="bg-[#D9FDD3] rounded-md px-3 py-2 max-w-[85%] text-sm text-ink space-y-2">
              {sampleMessages.map((msg, i) => (
                <p key={i}>{msg.text}</p>
              ))}
              <div className="text-right text-xs text-ink-faint">
                {sampleMessages[sampleMessages.length - 1].time}
              </div>
            </div>
          </div>
        </div>

        <div className="flex justify-end mt-6">
          <button
            onClick={onClose}
            className="bg-white border border-rule-strong text-ink text-sm font-semibold px-4 py-2 rounded hover:bg-paper"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
