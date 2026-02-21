
export default function ConfidenceBadge({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color = pct >= 80 ? "bg-emerald-600" : pct >= 60 ? "bg-amber-600" : "bg-slate-700";

  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium text-white ${color}`}>
      {pct}%
    </span>
  );
}
