function GlobalHeader({ criticalCount, liveAttackActive, query, setQuery, onAlertClick, onChatSubmit }) {
  const handleKeyDown = (e) => {
    if (e.key === "Enter" && query.trim()) {
      onChatSubmit(query);
    }
  };

  const isFlashing = criticalCount > 0 || liveAttackActive;

  return (
    <header className="rounded-xl border border-slate-800 bg-panel/90 px-5 py-4 backdrop-blur-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.28em] text-slateText">honeypit AI Command</p>
          <h1 className="text-2xl font-bold text-cyan-100">Threat Console</h1>
        </div>

        <div className="flex w-full items-center gap-3 lg:max-w-3xl">
          <div className="group flex-1 rounded-lg border border-cyan-500/30 bg-slate-900/80 px-4 py-3 shadow-neonCyan transition-all focus-within:border-cyan-400 focus-within:shadow-[0_0_15px_rgba(34,211,238,0.2)]">
            <p className="mb-1 flex items-center justify-between text-[11px] uppercase tracking-[0.2em] text-cyan-300/70">
              <span>Chat With Your Logs</span>
              <span className="opacity-0 transition-opacity group-focus-within:opacity-100">Press Enter ↵</span>
            </p>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              className="w-full bg-transparent font-mono text-sm text-slate-100 outline-none placeholder:text-slate-500"
              placeholder="e.g., Show me all human attacks probing for AWS keys yesterday..."
            />
          </div>

          <button
            type="button"
            onClick={onAlertClick}
            className={[
              "relative rounded-lg border px-4 py-3 text-sm font-semibold uppercase tracking-[0.12em] transition min-w-[120px]",
              isFlashing
                ? "animate-pulseRed border-neonRed/80 bg-neonRed/15 text-neonRed shadow-neonRed"
                : "border-slate-700 bg-slate-900 text-slate-400",
            ].join(" ")}
            aria-label="Critical human threat alerts"
          >
            {liveAttackActive ? "LIVE BREACH (1)" : `Alerts (${criticalCount})`}
          </button>
        </div>
      </div>
    </header>
  );
}

export default GlobalHeader;
