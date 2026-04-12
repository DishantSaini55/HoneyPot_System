function NodeGraph({ attackers, selectedId, onSelect }) {
  return (
    <section className="rounded-xl border border-slate-800 bg-panel/90 p-4">
      <div className="mb-4">
        <p className="text-xs uppercase tracking-[0.2em] text-slateText">Threat Intelligence Graph</p>
        <h2 className="text-xl font-bold text-cyan-100">Live Threat Node Graph</h2>
      </div>

      <div className="grid-overlay relative h-[420px] overflow-hidden rounded-lg border border-slate-700/60 bg-slate-950/90 p-4">
        <p className="mb-2 font-mono text-xs text-slate-400">
          Placeholder canvas for react-force-graph / three.js visualization
        </p>

        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative h-72 w-72 rounded-full border border-cyan-400/30">
            <div className="absolute left-1/2 top-1/2 h-16 w-16 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-400/70 bg-cyan-500/10 text-center">
              <p className="pt-5 text-xs font-bold uppercase tracking-[0.2em] text-cyan-200">Swarm</p>
            </div>

            {attackers.map((attacker, index) => {
              const angle = (index / attackers.length) * Math.PI * 2;
              const x = 50 + 38 * Math.cos(angle);
              const y = 50 + 38 * Math.sin(angle);
              const isSelected = attacker.id === selectedId;
              const isHuman = attacker.classification === "Human Hacker";

              return (
                <button
                  key={attacker.id}
                  type="button"
                  onClick={() => onSelect(attacker.id)}
                  className={[
                    "absolute -translate-x-1/2 -translate-y-1/2 rounded-md border px-2 py-1 font-mono text-[11px]",
                    isSelected
                      ? "border-white bg-slate-200 text-slate-900"
                      : isHuman
                        ? "border-neonRed/70 bg-neonRed/10 text-neonRed"
                        : "border-botYellow/60 bg-botYellow/10 text-yellow-200",
                  ].join(" ")}
                  style={{ left: `${x}%`, top: `${y}%` }}
                >
                  {attacker.alias}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}

export default NodeGraph;
