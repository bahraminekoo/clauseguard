
export type RiskFinding = {
  category: string;
  page?: number | null;
  explanation: string;
  clause_text: string;
};


export default function RiskCard({ finding }: { finding: RiskFinding }) {
  return (
    <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="space-y-1">
          <div className="text-sm font-semibold text-white">{finding.category}</div>
          <div className="text-xs text-slate-400">
            Page: {finding.page ?? "—"}
          </div>
        </div>
      </div>

      <div className="mt-3 text-sm text-slate-200">{finding.explanation}</div>
      <pre className="mt-3 whitespace-pre-wrap rounded-md bg-slate-950 p-3 text-xs text-slate-200">
        {finding.clause_text}
      </pre>
    </div>
  );
}
