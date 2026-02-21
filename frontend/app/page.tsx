
import Link from "next/link";


export default function HomePage() {
  return (
    <main className="space-y-6">
      <header className="space-y-2">
        <h1 className="text-3xl font-semibold">ClauseGuard</h1>
        <p className="text-slate-300">
          Privacy-first, retrieval-driven contract risk scanner (scaffold).
        </p>
      </header>

      <div>
        <Link
          href="/analyze"
          className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
        >
          Go to Analyzer
        </Link>
      </div>
    </main>
  );
}
