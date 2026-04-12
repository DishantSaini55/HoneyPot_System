function TrafficTicker({ items }) {
  return (
    <section className="rounded-xl border border-slate-800 bg-panel/85 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slateText">Background Noise Handling</p>
      <h2 className="mb-3 text-lg font-bold text-slate-100">Algorithmic Tarpit Feed</h2>

      <div className="relative h-10 overflow-hidden rounded-md border border-slate-700 bg-slate-900">
        <div className="absolute left-0 top-2 whitespace-nowrap font-mono text-xs text-slate-400 animate-glide">
          {items.join("   |   ")}
        </div>
      </div>

      <div className="mt-4 space-y-2">
        {items.map((item, idx) => (
          <p key={`${item}-${idx}`} className="font-mono text-xs text-slate-500">
            {item}
          </p>
        ))}
      </div>
    </section>
  );
}

export default TrafficTicker;
