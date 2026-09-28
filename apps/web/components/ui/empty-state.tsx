export function EmptyState({ title = "No telemetry available", detail = "Events will appear after a honeypot records activity." }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-700 px-6 py-12 text-center">
      <p className="font-medium text-slate-300">{title}</p>
      <p className="mt-1 text-sm text-slate-500">{detail}</p>
    </div>
  );
}

