
"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import RiskDashboard from "../../components/RiskDashboard";
import DisclaimerBanner from "../../components/DisclaimerBanner";
import UploadDropzone from "../../components/UploadDropzone";


type RiskFinding = {
  category: string;
  page?: number | null;
  explanation: string;
  clause_text: string;
};


export default function AnalyzePage() {
  const [text, setText] = useState<string>(
    "Vendor shall be liable for all damages arising from this agreement."
  );
  const [docId, setDocId] = useState<string>("");
  const [queryText, setQueryText] = useState<string>("liability clauses");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([
    "UNLIMITED_LIABILITY",
  ]);
  const [findings, setFindings] = useState<RiskFinding[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiBaseUrl = useMemo(
    () => process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
    []
  );

  const categories = [
    { key: "UNLIMITED_LIABILITY", label: "Unlimited Liability" },
    { key: "INDEMNIFICATION", label: "Indemnification" },
    { key: "TERMINATION", label: "Termination for Convenience" },
  ];

  async function onAnalyze() {
    setLoading(true);
    setError(null);
    try {
      const body = docId
        ? {
            doc_id: docId,
            query_text: queryText,
            category_keys: selectedCategories,
          }
        : {
            text,
            category_keys: selectedCategories,
          };

      const res = await fetch(`${apiBaseUrl}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
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

        <UploadDropzone
          onUploaded={(id) => setDocId(id)}
          apiBaseUrl={apiBaseUrl}
        />

        <div className="grid gap-4 md:grid-cols-2">
          <label className="space-y-2 text-sm text-slate-200">
            <span className="text-xs uppercase tracking-wide text-slate-400">
              Query text (used for retrieval when doc is uploaded)
            </span>
            <input
              value={queryText}
              onChange={(e) => setQueryText(e.target.value)}
              className="w-full rounded-md border border-slate-800 bg-slate-950 p-3 text-sm text-slate-100 outline-none focus:border-indigo-500"
            />
          </label>

          <label className="space-y-2 text-sm text-slate-200">
            <span className="text-xs uppercase tracking-wide text-slate-400">
              Doc ID (set automatically on upload; leave blank to analyze pasted text)
            </span>
            <input
              value={docId}
              onChange={(e) => setDocId(e.target.value)}
              placeholder="Paste or use upload"
              className="w-full rounded-md border border-slate-800 bg-slate-950 p-3 text-sm text-slate-100 outline-none focus:border-indigo-500"
            />
          </label>
        </div>

        <label className="space-y-2 text-sm text-slate-200">
          <span className="text-xs uppercase tracking-wide text-slate-400">
            Categories
          </span>
          <div className="flex flex-wrap gap-2">
            {categories.map((c) => {
              const active = selectedCategories.includes(c.key);
              return (
                <button
                  key={c.key}
                  type="button"
                  onClick={() =>
                    setSelectedCategories((prev) =>
                      prev.includes(c.key)
                        ? prev.filter((k) => k !== c.key)
                        : [...prev, c.key]
                    )
                  }
                  className={`rounded-full border px-3 py-1 text-xs font-medium transition ${
                    active
                      ? "border-indigo-400 bg-indigo-500/20 text-indigo-100"
                      : "border-slate-700 bg-slate-900/50 text-slate-200"
                  }`}
                >
                  {c.label}
                </button>
              );
            })}
          </div>
        </label>

        <label className="space-y-2 text-sm text-slate-200">
          <span className="text-xs uppercase tracking-wide text-slate-400">
            Paste text (used when no doc_id provided)
          </span>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="h-32 w-full resize-none rounded-md border border-slate-800 bg-slate-950 p-3 font-mono text-sm text-slate-100 outline-none focus:border-indigo-500"
          />
        </label>

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
