import { useMemo } from "react";

function hashToColor(seed) {
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = seed.charCodeAt(i) + ((hash << 5) - hash);
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 70%, 58%)`;
}

function makeReport(attacker) {
  const lines = [
    `# MITRE ATT&CK Threat Report: ${attacker.alias}`,
    "",
    `- Classification: ${attacker.classification}`,
    `- Threat Score: ${attacker.threatScore}/100`,
    `- Source IP: ${attacker.sourceIp}`,
    `- Weapon of Choice: ${attacker.weapon}`,
    "",
    "## Kill Chain Timeline",
    ...attacker.timeline.map((step) => `- ${step}`),
    "",
    "## MITRE ATT&CK Mapping (Simulated)",
    "- Reconnaissance: Active Scanning (T1595)",
    "- Initial Access: Brute Force (T1110)",
    "- Discovery: File and Directory Discovery (T1083)",
    "- Collection: Data from Information Repositories (T1213)",
  ];

  const blob = new Blob([lines.join("\n")], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${attacker.alias.toLowerCase().replace(/\s+/g, "-")}-mitre-report.md`;
  a.click();
  URL.revokeObjectURL(url);
}

function AttackerProfile({ attacker }) {
  const avatarColor = useMemo(() => hashToColor(attacker.avatarSeed), [attacker.avatarSeed]);
  const isHuman = attacker.classification === "Human Hacker";

  return (
    <section className="rounded-xl border border-slate-800 bg-panel/95 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slateText">Behavioral Fingerprinting</p>
      <h2 className="mb-3 text-xl font-bold text-cyan-100">Attacker Profile Card</h2>

      <div className="mb-4 flex items-start gap-4 rounded-lg border border-slate-700 bg-slate-900/70 p-3">
        <div className="grid h-16 w-16 grid-cols-4 gap-[2px] rounded-md bg-slate-950 p-1">
          {Array.from({ length: 16 }).map((_, idx) => (
            <div
              key={idx}
              className="rounded-[1px]"
              style={{
                backgroundColor: idx % 2 === 0 ? avatarColor : "rgba(15,23,42,0.9)",
              }}
            />
          ))}
        </div>
        <div className="flex-1">
          <p className="text-lg font-semibold text-slate-100">{attacker.alias}</p>
          <p className="font-mono text-xs text-slate-400">{attacker.sourceIp} | {attacker.geo}</p>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <span className="rounded border border-cyan-400/60 bg-cyan-500/10 px-2 py-1 text-cyan-200">
              Threat Score: {attacker.threatScore}/100
            </span>
            <span className="rounded border border-slate-500/70 bg-slate-700/40 px-2 py-1 text-slate-200">
              Weapon: {attacker.weapon}
            </span>
            <span
              className={[
                "rounded border px-2 py-1",
                isHuman
                  ? "border-neonRed/70 bg-neonRed/10 text-neonRed"
                  : "border-botYellow/70 bg-botYellow/10 text-yellow-200",
              ].join(" ")}
            >
              ML Classification: {attacker.classification}
            </span>
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_1fr]">
        <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
          <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slateText">Cyber Kill Chain Timeline</p>
          <ol className="space-y-2 border-l border-slate-600 pl-4">
            {attacker.timeline.map((event) => (
              <li key={event} className="relative font-mono text-xs text-slate-300">
                <span className="absolute -left-[22px] top-1 h-2 w-2 rounded-full bg-cyan-400" />
                {event}
              </li>
            ))}
          </ol>
        </div>

        <div className="rounded-lg border border-slate-700 bg-slate-900/60 p-3">
          <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slateText">Generative Deception Log</p>
          <div className="space-y-2">
            {attacker.aiActions.map((action) => (
              <p key={action} className="font-mono text-xs text-cyan-200">
                {action}
              </p>
            ))}
          </div>
          <button
            type="button"
            onClick={() => makeReport(attacker)}
            className="mt-4 w-full rounded-lg border border-neonRed/70 bg-neonRed/15 px-3 py-2 text-sm font-semibold uppercase tracking-[0.12em] text-neonRed shadow-neonRed"
          >
            Generate Threat Report
          </button>
        </div>
      </div>
    </section>
  );
}

export default AttackerProfile;
