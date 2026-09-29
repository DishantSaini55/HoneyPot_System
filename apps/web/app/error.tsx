"use client";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return <html><body className="grid min-h-screen place-items-center bg-slate-950 p-6 text-slate-100"><main className="max-w-md rounded-xl border border-slate-800 bg-slate-900 p-7"><p className="text-sm font-semibold text-rose-300">Application error</p><h1 className="mt-2 text-2xl font-semibold">This page could not be loaded.</h1><p className="mt-3 text-sm text-slate-400">The error was contained. Check service health or retry the request.</p><button type="button" onClick={reset} className="mt-5 rounded-lg bg-cyan-400 px-4 py-2 font-medium text-slate-950">Retry</button></main></body></html>;
}
