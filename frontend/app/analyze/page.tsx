
"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import RiskDashboard from "../../components/RiskDashboard";
import DisclaimerBanner from "../../components/DisclaimerBanner";


type RiskFinding = {
  category: string;
  confidence: number;
  page?: number | null;
  explanation: string;
  clause_text: string;
};


export default function AnalyzePage() {
  const [text, setText] = useState<string>(
    "Vendor shall be liable for all damages arising from this agreement."
  );
  const [findings, setFindings] = useState<RiskFinding[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
    []
  );

  async function onAnalyze() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBaseUrl}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });

      if (!res.ok) {
        const msg = await res.text();
        throw new Error(msg || `Request failed (${res.status})`);
      }

      const data = (await res.json()) as { findings: RiskFinding[] };
      setFindings(data.findings ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Analyze</h1>
        <Link href="/" className="text-sm text-slate-300 hover:text-white">
          Back
        </Link>
      </div>

      <DisclaimerBanner />

      <section className="space-y-3 rounded-lg border border-slate-800 bg-slate-900/40 p-4">
        <div className="text-sm text-slate-300">
          API: <span className="font-mono text-slate-200">{apiBaseUrl}</span>
        </div>

        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="h-40 w-full resize-none rounded-md border border-slate-800 bg-slate-950 p-3 font-mono text-sm text-slate-100 outline-none focus:border-indigo-500"
        />

        <div className="flex items-center gap-3">
          <button
            onClick={onAnalyze}
            disabled={loading}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-50"
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
          {error ? <div className="text-sm text-red-300">{error}</div> : null}
        </div>
      </section>

      <RiskDashboard findings={findings} />
    </main>
  );
}
