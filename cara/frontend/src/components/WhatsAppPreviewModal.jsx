import React from 'react';
import { X, CheckCheck, Phone, Video, MoreVertical, Send, ShieldCheck } from 'lucide-react';

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
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
      <div className="bg-slate-900 rounded-2xl shadow-2xl max-w-sm w-full border border-slate-800 overflow-hidden text-slate-100 animate-in fade-in zoom-in duration-200">
        {/* Phone Header */}
        <div className="bg-emerald-800 text-white px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-full bg-emerald-600 flex items-center justify-center font-bold text-sm border border-emerald-400">
              {patientName ? patientName.charAt(0) : 'P'}
            </div>
            <div>
              <h4 className="font-bold text-sm leading-tight">{patientName || 'Mother'} (WhatsApp)</h4>
              <p className="text-[11px] text-emerald-200 flex items-center">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 mr-1.5"></span>
                {recipientContact} • Encrypted
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2 text-emerald-200">
            <Phone className="h-4 w-4" />
            <Video className="h-4 w-4" />
            <button onClick={onClose} className="hover:text-white p-1">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* WhatsApp Chat Background Body */}
        <div className="bg-[#efeae2] p-4 h-80 overflow-y-auto space-y-3 font-sans text-slate-800 relative">
          <div className="text-center my-1">
            <span className="bg-[#e1f3fb] text-[10px] text-slate-600 font-medium px-2.5 py-1 rounded-md shadow-2xs border border-sky-200 inline-flex items-center">
              <ShieldCheck className="h-3 w-3 mr-1 text-sky-600" />
              Verified WhatsApp Business Account • Non-Clinical Channel
            </span>
          </div>

          {sampleMessages.map((msg, i) => (
            <div key={i} className="flex justify-start">
              <div className="bg-white rounded-lg p-3 max-w-[85%] shadow-sm text-xs border border-slate-200/80 relative">
                <div className="font-semibold text-emerald-800 text-[10px] mb-1">
                  {facilityName || 'Cara PNC Coordinator'}
                </div>
                <p className="text-slate-800 leading-relaxed">{msg.text}</p>
                <div className="flex items-center justify-end space-x-1 mt-1 text-[9px] text-slate-400">
                  <span>{msg.time}</span>
                  <CheckCheck className="h-3 w-3 text-sky-500" />
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Mock Input Bar */}
        <div className="bg-slate-100 px-3 py-2.5 border-t border-slate-200 flex items-center space-x-2 text-slate-800">
          <input
            type="text"
            readOnly
            value="Reply 1 to confirm appointment..."
            className="flex-1 bg-white border border-slate-300 rounded-full px-3 py-1.5 text-xs text-slate-400 focus:outline-none"
          />
          <button className="bg-emerald-600 text-white p-2 rounded-full shadow hover:bg-emerald-700">
            <Send className="h-3.5 w-3.5" />
          </button>
        </div>

        <div className="bg-slate-950 px-4 py-2 text-center text-[11px] text-slate-400 flex items-center justify-between border-t border-slate-800">
          <span>AI Content Guardrail Status: <strong className="text-emerald-400">PASSED</strong></span>
          <button onClick={onClose} className="text-emerald-400 hover:underline font-semibold">
            Close Preview
          </button>
        </div>
      </div>
    </div>
  );
}
