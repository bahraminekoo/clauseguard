
import RiskCard, { RiskFinding } from "./RiskCard";


export default function RiskDashboard({ findings }: { findings: RiskFinding[] }) {
  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold">Findings</h2>

      {findings.length === 0 ? (
        <div className="rounded-lg border border-slate-800 bg-slate-900/20 p-4 text-sm text-slate-300">
          No findings yet.
        </div>
      ) : (
        <div className="grid gap-3">
          {findings.map((f, idx) => (
            <RiskCard key={`${f.category}-${idx}`} finding={f} />
          ))}
        </div>
      )}
    </section>
  );
}
