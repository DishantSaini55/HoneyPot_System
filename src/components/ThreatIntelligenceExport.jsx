import { useMemo, useState, useEffect } from "react";
import { FileJson, LoaderCircle } from "lucide-react";

const mockSessions = [
  {
    id: "sess-9f31a2",
    ip: "185.141.22.91",
    node: "Node-AI-04",
    duration: "08m 12s",
    classification: "Human Hacker",
  },
  {
    id: "sess-b72de0",
    ip: "103.88.71.22",
    node: "Node-WEB-02",
    duration: "02m 34s",
    classification: "Automated Bot",
  },
  {
    id: "sess-c41dd7",
    ip: "212.67.19.204",
    node: "Node-FTP-03",
    duration: "03m 49s",
    classification: "Automated Bot",
  },
];

function ThreatIntelligenceExport({ threatReportReady, compromisedNode = "Honeypot-SSH-01" }) {
  const finalSessions = useMemo(() => {
    if (threatReportReady) {
      return [
        {
          id: "sess-live-capture",
          ip: "127.0.0.1",
          node: compromisedNode,
          duration: "RECENT",
          classification: "Human Hacker (Live Capture)",
        },
        ...mockSessions,
      ];
    }
    return mockSessions;
  }, [threatReportReady]);

  const [selectedIds, setSelectedIds] = useState(() => finalSessions.map((s) => s.id));
  
  useEffect(() => {
    // Automatically select all when finalSessions changes (e.g., when the live capture is added)
    setSelectedIds(finalSessions.map((s) => s.id));
  }, [finalSessions]);

  const [downloadState, setDownloadState] = useState("idle");
  const [toast, setToast] = useState("");

  const isAllSelected = useMemo(() => selectedIds.length === finalSessions.length, [selectedIds.length, finalSessions.length]);

  const toggleSelectAll = () => {
    setSelectedIds((prev) => (prev.length === finalSessions.length ? [] : finalSessions.map((s) => s.id)));
  };

  const toggleSession = (id) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((item) => item !== id);
      }
      return [...prev, id];
    });
  };

  const downloadJsonFile = (sessions) => {
    const payload = {
      schema: "honeypot.universal-threat-intel.v1",
      generatedAt: new Date().toISOString(),
      sessionCount: sessions.length,
      sessions,
    };

    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json;charset=utf-8",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "session_data_export.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const handleJsonDownload = () => {
    if (downloadState === "loading") {
      return;
    }

    const selectedSessions = finalSessions.filter((session) => selectedIds.includes(session.id));
    if (selectedSessions.length === 0) {
      setToast("Select at least one session before export.");
      return;
    }

    setDownloadState("loading");
    setToast("");

    window.setTimeout(() => {
      downloadJsonFile(selectedSessions);
      setDownloadState("success");
      setToast("session_data_export.json successfully generated.");

      window.setTimeout(() => {
        setDownloadState("idle");
        setToast("");
      }, 3000);
    }, 1500);
  };

  return (
    <section className="rounded-xl border border-slate-800 bg-panel/95 p-4">
      <p className="text-xs uppercase tracking-[0.2em] text-slateText">Threat Intelligence Export</p>
      <h2 className="mb-3 text-xl font-bold text-cyan-100">Session Export Workbench</h2>

      <div className="overflow-hidden rounded-lg border border-slate-700 bg-slate-950/70">
        <table className="w-full border-collapse text-left">
          <thead className="bg-slate-900/90 text-[11px] uppercase tracking-[0.16em] text-slate-400">
            <tr>
              <th className="px-3 py-2">
                <label className="inline-flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={isAllSelected}
                    onChange={toggleSelectAll}
                    className="h-4 w-4 rounded border-slate-500 bg-slate-900 text-cyan-400"
                  />
                  Select All
                </label>
              </th>
              <th className="px-3 py-2">Session ID</th>
              <th className="px-3 py-2">Attacker IP</th>
              <th className="px-3 py-2">Node Target</th>
              <th className="px-3 py-2">Duration</th>
              <th className="px-3 py-2">Threat Classification</th>
            </tr>
          </thead>

          <tbody>
            {finalSessions.map((session) => {
              const isHuman = session.classification.includes("Human Hacker");
              return (
                <tr key={session.id} className="border-t border-slate-800 text-sm text-slate-200">
                  <td className="px-3 py-3">
                    <input
                      type="checkbox"
                      checked={selectedIds.includes(session.id)}
                      onChange={() => toggleSession(session.id)}
                      className="h-4 w-4 rounded border-slate-500 bg-slate-900 text-cyan-400"
                    />
                  </td>
                  <td className="px-3 py-3 font-mono text-xs text-cyan-200">{session.id}</td>
                  <td className="px-3 py-3 font-mono text-xs text-slate-300">{session.ip}</td>
                  <td className="px-3 py-3 font-mono text-xs text-slate-300">{session.node}</td>
                  <td className="px-3 py-3 font-mono text-xs text-slate-300">{session.duration}</td>
                  <td className="px-3 py-3">
                    <span
                      className={[
                        "rounded border px-2 py-1 font-mono text-[11px] uppercase tracking-[0.14em]",
                        isHuman
                          ? "border-neonRed/70 bg-neonRed/12 text-neonRed"
                          : "border-botYellow/70 bg-botYellow/12 text-yellow-200",
                      ].join(" ")}
                    >
                      {session.classification}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="mt-4 rounded-lg border border-slate-700 bg-slate-900/70 p-4">
        <p className="mb-3 text-xs uppercase tracking-[0.2em] text-slateText">Export Intelligence</p>

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleJsonDownload}
            className={[
              "inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-semibold uppercase tracking-[0.12em] transition",
              downloadState === "success"
                ? "border-emerald-400/80 bg-emerald-500/20 text-emerald-200"
                : "border-cyan-400/70 bg-cyan-500/15 text-cyan-100 shadow-neonCyan",
            ].join(" ")}
          >
            {downloadState === "loading" ? (
              <LoaderCircle className="h-4 w-4 animate-spin" />
            ) : (
              <FileJson className="h-4 w-4" />
            )}
            {downloadState === "loading" && "Compiling..."}
            {downloadState === "idle" && "Download JSON (Universal Schema)"}
            {downloadState === "success" && "Downloaded!"}
          </button>

          {downloadState === "loading" && (
            <p className="font-mono text-xs text-cyan-200">Compiling Universal Threat Schema...</p>
          )}
        </div>

        {toast && (
          <div className="mt-3 rounded border border-emerald-400/60 bg-emerald-500/10 px-3 py-2 font-mono text-xs text-emerald-200">
            {toast}
          </div>
        )}
      </div>
    </section>
  );
}

export default ThreatIntelligenceExport;
