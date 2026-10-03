import { RISK_CRITERIA } from '../lib/risk';

export default function FOGSIRiskCalculator({ selected, onChange, tier }) {
  const toggle = (id) => onChange(selected.includes(id) ? selected.filter((c) => c !== id) : [...selected, id]);

  return (
    <div className="card p-4">
      <h3 className="text-sm font-bold">FOGSI risk factors</h3>
      <p className="text-xs text-ink-faint mt-1">Tick everything that applies. The most frequent schedule wins.</p>

      <div className="mt-3 space-y-2">
        {RISK_CRITERIA.map((item) => (
          <label key={item.id} className="flex items-start gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={selected.includes(item.id)}
              onChange={() => toggle(item.id)}
              className="mt-0.5 h-4 w-4 accent-[#0E5A54]"
            />
            <span>
              {item.label}
              <span className="block text-xs text-ink-faint">Adds {item.effect}</span>
            </span>
          </label>
        ))}
      </div>

      {tier && (
        <div className="border-t border-rule pt-3 mt-4 text-sm">
          <p className={`font-semibold ${tier.tone}`}>{tier.label}</p>
          <p className="text-ink-soft mt-1">{tier.summary}</p>
        </div>
      )}
    </div>
  );
}
