import { useEffect, useRef, useState } from "react";
import { Activity, Brain, Hourglass, Terminal, Zap } from "lucide-react";

const MODE_IDLE = "idle";
const MODE_NODE4 = "node4";
const MODE_NODE3 = "node3";

function formatDuration(totalSeconds) {
  const h = String(Math.floor(totalSeconds / 3600)).padStart(2, "0");
  const m = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, "0");
  const s = String(totalSeconds % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

function ThreatTelemetryFlow({ node4OpenSignal = 0 }) {
  const [mode, setMode] = useState(MODE_IDLE);

  const [node3CommandVisible, setNode3CommandVisible] = useState(false);
  const [node3Progress, setNode3Progress] = useState(0);
  const [node3Speed, setNode3Speed] = useState("120.000 KB/s");
  const [node3WastedTime, setNode3WastedTime] = useState(195);

  const [liveLogs, setLiveLogs] = useState([]);
  const logsEndRef = useRef(null);

  const timersRef = useRef([]);

  // Auto-scroll logs to bottom when new logs arrive
  useEffect(() => {
    if (mode === MODE_NODE4 && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [liveLogs, mode]);

  useEffect(() => {
    if (node4OpenSignal > 0) {
      setMode(MODE_NODE4);
    }
  }, [node4OpenSignal]);

  useEffect(() => {
    let isCancelled = false;

    timersRef.current.forEach((t) => {
      clearTimeout(t);
      clearInterval(t);
    });
    timersRef.current = [];

    setNode3CommandVisible(false);
    setNode3Progress(0);
    setNode3Speed("120.000 KB/s");
    setNode3WastedTime(195);

    if (mode === MODE_NODE4) {
      // Clear logs on backend on fresh start
      fetch("/api/telemetry/logs", { method: "DELETE" }).catch(() => {});
      setLiveLogs([]);

      // Start polling backend for live SSH feed
      const pollTimer = window.setInterval(() => {
        fetch("/api/telemetry/logs")
          .then((res) => res.json())
          .then((data) => {
            if (!isCancelled && data.logs) {
              setLiveLogs([...data.logs]);
            }
          })
          .catch(() => {});
      }, 1000);
      timersRef.current.push(pollTimer);
    }

    if (mode === MODE_NODE3) {
      const commandPause = window.setTimeout(() => {
        setNode3CommandVisible(true);
      }, 320);
      timersRef.current.push(commandPause);

      const progressPause = window.setTimeout(() => {
        const progressTimer = window.setInterval(() => {
          setNode3Progress((prev) => {
            if (prev >= 99.2) {
              setNode3Speed("0.002 KB/s");
              return prev;
            }

            let next = prev;
            if (prev < 70) {
              next += 2.2;
              setNode3Speed("84.120 KB/s");
            } else if (prev < 90) {
              next += 0.85;
              setNode3Speed("19.540 KB/s");
            } else if (prev < 98) {
              next += 0.24;
              setNode3Speed("1.240 KB/s");
            } else {
              next += 0.02;
              setNode3Speed("0.002 KB/s");
            }

            return Math.min(99.2, next);
          });
        }, 140);

        timersRef.current.push(progressTimer);
      }, 980);
      timersRef.current.push(progressPause);

      const wastedTimer = window.setInterval(() => {
        setNode3WastedTime((prev) => prev + 1);
      }, 1000);
      timersRef.current.push(wastedTimer);
    }

    return () => {
      isCancelled = true;
      timersRef.current.forEach((t) => {
        clearTimeout(t);
        clearInterval(t);
      });
      timersRef.current = [];
    };
  }, [mode]);

  const title =
    mode === MODE_NODE4
      ? "Node-AI-04: Generative Deception"
      : mode === MODE_NODE3
        ? "Node-FTP-03: Algorithmic Tarpit"
        : "Interactive AI Honeypot Flow";

  const badgeText = mode === MODE_NODE4 ? "LLM Active" : mode === MODE_NODE3 ? "Tarpit Engaged" : "Idle";

  const badgeClass =
    mode === MODE_NODE4
      ? "border-cyan-400/60 bg-cyan-500/10 text-cyan-100 shadow-neonCyan"
      : mode === MODE_NODE3
        ? "border-botYellow/70 bg-botYellow/15 text-yellow-200"
        : "border-slate-600 bg-slate-800/70 text-slate-300";

  return (
    <section>
      <div className="mb-3 flex flex-wrap gap-2">
        <button
          type="button"
          onClick={() => setMode(MODE_NODE4)}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-500 bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-white"
        >
          <Activity className="h-4 w-4" />
          Simulate Node-AI-04 Attack
        </button>
        <button
          type="button"
          onClick={() => setMode(MODE_NODE3)}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-500 bg-slate-100 px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-white"
        >
          <Zap className="h-4 w-4" />
          Simulate Node-FTP-03 Attack
        </button>
        <button
          type="button"
          onClick={() => setMode(MODE_IDLE)}
          className="inline-flex items-center gap-2 rounded-lg border border-slate-600 bg-slate-900 px-4 py-2 text-sm font-semibold text-slate-200 transition hover:border-slate-400"
        >
          <Hourglass className="h-4 w-4" />
          Reset
        </button>
      </div>

      <div className="rounded-xl border border-slate-700 bg-panel/95 p-4">
        <div className="mb-4 flex items-center justify-between gap-2">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-slateText">Threat Telemetry</p>
            <h2 className="text-xl font-bold text-slate-100">{title}</h2>
          </div>
          <span className={["rounded border px-2 py-1 font-mono text-xs", badgeClass].join(" ")}>[{badgeText}]</span>
        </div>

        <div className="rounded-xl border border-slate-700 bg-slate-950/75 p-4">
          {mode === MODE_IDLE && (
            <p className="text-sm text-slate-300">
              Click compromised Node-AI-04 in Deployment Ops above to initialize live telemetry.
            </p>
          )}

          {mode === MODE_NODE4 && (
            <div className="space-y-3">
              <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-3 h-80 overflow-y-auto flex flex-col font-mono text-sm shadow-inner transition-all scrollbar-thin scrollbar-track-slate-800 scrollbar-thumb-slate-600">
                <div className="sticky top-0 z-10 mb-4 flex items-center justify-between gap-2 border-b border-slate-700 bg-slate-900/90 pb-2 backdrop-blur-sm">
                  <p className="inline-flex items-center gap-2 text-xs uppercase tracking-[0.14em] text-cyan-400">
                    <Terminal className="h-4 w-4" />
                    Live SSH Feed (Port 2222)
                  </p>
                  <div className="flex gap-2">
                    <span className="animate-pulse rounded border border-cyan-400/60 bg-cyan-500/10 px-2 py-1 font-mono text-[11px] text-cyan-100">
                      Listening...
                    </span>
                  </div>
                </div>

                <div className="flex-1 space-y-4">
                  {liveLogs.length === 0 && (
                    <p className="text-slate-500 animate-pulse">Waiting for SSH attack connection on 0.0.0.0:2222...</p>
                  )}

                  {liveLogs.map((log) => (
                    <div key={log.id} className="animate-in fade-in duration-300">
                      {log.type === "connection" ? (
                        <div className="text-amber-400 text-xs">[{log.message}]</div>
                      ) : (
                        <>
                          <div className="text-slate-300">
                            <span className="text-cyan-500 font-bold mr-2">root@target:~#</span> 
                            {log.command}
                          </div>
                          {log.status === "generating" && (
                            <div className="text-slate-500 text-xs mt-1 animate-pulse">
                              [System] Intercepted. AI generating spoofed response...
                            </div>
                          )}
                          {log.status === "done" && log.response && (
                            <div className="text-cyan-200 mt-2 whitespace-pre-wrap break-all text-xs leading-relaxed opacity-90 p-2 rounded bg-slate-950/50 border border-slate-800">
                              {log.response}
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  ))}
                  <div ref={logsEndRef} className="h-1" />
                </div>
              </div>
            </div>
          )}

          {mode === MODE_NODE3 && (
            <div className="space-y-3">
              {node3CommandVisible && (
                <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
                  <p className="mb-1 font-mono text-xs uppercase tracking-[0.14em] text-slate-400">Attacker Request</p>
                  <p className="font-mono text-sm text-slate-100">GET production_db_dump.zip (8.5GB)</p>
                </div>
              )}

              <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
                <p className="mb-2 text-xs uppercase tracking-[0.14em] text-slate-400">Transfer Progress</p>
                <div className="h-3 w-full overflow-hidden rounded-full bg-slate-800">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-slate-300 via-slate-200 to-white transition-all"
                    style={{ width: `${node3Progress}%` }}
                  />
                </div>
                <p className="mt-2 font-mono text-xs text-slate-300">{node3Progress.toFixed(2)}%</p>
              </div>

              <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
                <p className="font-mono text-xs text-slate-200">
                  Throttling connection... | Speed: {node3Speed} | Time Wasted: {formatDuration(node3WastedTime)}
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

export default ThreatTelemetryFlow;
