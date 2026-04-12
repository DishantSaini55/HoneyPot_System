const nodeStyle = {
  active: "border-cyan-400/60 bg-cyan-500/10 text-cyan-200",
  engaging: "border-botYellow/70 bg-botYellow/15 text-yellow-200",
  compromised: "animate-pulseRed border-neonRed/80 bg-neonRed/15 text-neonRed",
};

function SwarmControl({ nodes, onInspectCompromised }) {
  return (
    <section className="rounded-xl border border-slate-800 bg-panel/90 p-4">
      <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slateText">Deployment Ops</p>
          <h2 className="text-xl font-bold text-cyan-100">1-Click Ephemeral Swarms</h2>
        </div>
        <button
          type="button"
          className="rounded-lg border border-neonCyan/70 bg-cyan-500/15 px-5 py-3 text-sm font-bold uppercase tracking-[0.14em] text-neonCyan shadow-neonCyan transition hover:scale-[1.02]"
        >
          Spawn Deception Swarm (5 Nodes)
        </button>
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
        {nodes.map((node) => {
          const isCompromised = node.state === "compromised";
          return (
            <button
              key={node.id}
              type="button"
              onClick={() => {
                if (isCompromised) {
                  onInspectCompromised?.(node.id);
                }
              }}
              className={[
                "rounded-lg border px-3 py-3 text-center transition",
                nodeStyle[node.state],
                isCompromised ? "cursor-pointer hover:scale-[1.02]" : "cursor-default",
              ].join(" ")}
            >
              <p className="text-sm font-semibold">{node.name}</p>
              <p className="font-mono text-xs uppercase tracking-[0.15em]">{node.service}</p>
              <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.18em]">{node.state}</p>
            </button>
          );
        })}
      </div>
    </section>
  );
}

export default SwarmControl;
