import { useMemo, useState, useEffect } from "react";
import { Routes, Route, Navigate, NavLink, useNavigate, useLocation } from "react-router-dom";
import { Bot, Loader2, X, Activity, Globe, Database } from "lucide-react";
import GlobalHeader from "./components/GlobalHeader";
import SwarmControl from "./components/SwarmControl";
import NodeGraph from "./components/NodeGraph";
import TrafficTicker from "./components/TrafficTicker";
import AttackerProfile from "./components/AttackerProfile";
import LiveAttackMap from "./components/LiveAttackMap";
import ThreatTelemetryFlow from "./components/ThreatTelemetryFlow";
import ThreatIntelligenceExport from "./components/ThreatIntelligenceExport";
import { attackers, swarmNodes, trafficTicker } from "./data/mockData";

function App() {
  const [query, setQuery] = useState("");
  const [selectedAttackerId, setSelectedAttackerId] = useState(attackers[0].id);
  const [telemetryNode4Signal, setTelemetryNode4Signal] = useState(0);

  const [isChatting, setIsChatting] = useState(false);
  const [chatResponse, setChatResponse] = useState("");
  const [chatSource, setChatSource] = useState("");

  const [liveAttackActive, setLiveAttackActive] = useState(false);
  const [threatReportReady, setThreatReportReady] = useState(false);
  const [compromisedNode, setCompromisedNode] = useState("Honeypot-SSH-01");

  const location = useLocation();

  // Poll for active live SSH attacks across the whole app
  useEffect(() => {
    let active = true;
    const poll = window.setInterval(() => {
      fetch("/api/telemetry/logs")
        .then((res) => res.json())
        .then((data) => {
          if (!active) return;
          if (data.logs && data.logs.length > 0) {
            // Find the most recent connection event
            const connections = data.logs.filter((l) => l.type === "connection");
            const connectLog = connections[connections.length - 1];
            const currentlyActive = connectLog ? !connectLog.message.includes("terminated") : false;
            
            if (connectLog) {
              if (connectLog.message.includes("Node-WEB-02")) {
                setCompromisedNode("Node-WEB-02");
              } else {
                setCompromisedNode("Honeypot-SSH-01");
              }
            }

            setLiveAttackActive((prevActive) => {
              // If attack just ended, set report ready
              if (prevActive && !currentlyActive) {
                setThreatReportReady(true);
              }
              return currentlyActive;
            });
          } else {
            setLiveAttackActive(false);
          }
        })
        .catch(() => {});
    }, 2000);

    return () => {
      active = false;
      clearInterval(poll);
    };
  }, []);

  const highestThreatAttacker = useMemo(() => {
    return attackers.reduce((top, attacker) => {
      return attacker.threatScore > top.threatScore ? attacker : top;
    }, attackers[0]);
  }, []);

  const visibleAttackers = useMemo(() => {
    if (!query.trim()) {
      return attackers;
    }

    const q = query.toLowerCase();
    return attackers.filter((attacker) => {
      return [
        attacker.alias,
        attacker.classification,
        attacker.weapon,
        attacker.sourceIp,
        attacker.timeline.join(" "),
      ]
        .join(" ")
        .toLowerCase()
        .includes(q);
    });
  }, [query]);

  const selected = useMemo(() => {
    let base = visibleAttackers.find((attacker) => attacker.id === selectedAttackerId) ?? visibleAttackers[0] ?? attackers[0];
    
    // Hardcode the Human Hacker profile when a live attack is actively happening for demo
    if (liveAttackActive) {
      base = {
        ...base,
        classification: "Human Hacker",
        alias: "UNKNOWN_LOCAL",
        sourceIp: "127.0.0.1",
        threatScore: 99.9,
      };
    }
    return base;
  }, [selectedAttackerId, visibleAttackers, liveAttackActive]);

  const liveMapAttackers = useMemo(() => {
    if (liveAttackActive) {
      const isWeb = compromisedNode === "Node-WEB-02";
      return [{
        id: isWeb ? "LIVE_WEB_02" : "LIVE_SSH_01",
        alias: "UNKNOWN_HUMAN_HACKER",
        classification: "Human Hacker",
        weapon: isWeb ? "SQL Injection Payload" : "SSH Reverse Shell",
        sourceIp: "127.0.0.1",
        targetNode: isWeb ? "Node-WEB-02" : "Node-AI-04",
        coordinates: { lat: 38.9072, lng: -77.0369 }, // Example Lat Lng
        threatScore: 99
      }, ...visibleAttackers];
    }
    return visibleAttackers;
  }, [liveAttackActive, visibleAttackers, compromisedNode]);

  const criticalCount = liveAttackActive ? 1 : attackers.filter((a) => a.classification === "Human Hacker").length;

  const navigate = useNavigate();

  const handleAlertClick = () => {
    setQuery("");
    if (liveAttackActive) {
      window.alert("HUMAN HACKER ALERT: Unidentified real-time SSH breach detected! Routing to Live Ops.");
      handleOpenTelemetryFromSwarm("N4");
      navigate("/telemetry");
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      setSelectedAttackerId(highestThreatAttacker.id);
      navigate("/dashboard");
    }
  };

  const handleOpenTelemetryFromSwarm = (nodeId) => {
    if (nodeId === "N4") {
      setTelemetryNode4Signal((prev) => prev + 1);
    }
  };

  const handleChatSubmit = async (submittedQuery) => {
    if (!submittedQuery.trim()) return;
    setIsChatting(true);
    setChatResponse("");
    setChatSource("");
    try {
      const response = await fetch("/api/ai/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: submittedQuery }),
      });
      if (!response.ok) throw new Error("API Network error");
      const data = await response.json();
      setChatResponse(data.content || "No intel returned from AI.");
      setChatSource(data.source || "unknown");
    } catch (err) {
      setChatResponse("AI Communication failure. System offline.");
      setChatSource("error");
    } finally {
      setIsChatting(false);
    }
  };

  return (
    <main className="min-h-screen bg-bg px-4 py-5 text-slate-100 lg:px-8">
      <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-4">
        <GlobalHeader
          criticalCount={criticalCount}
          liveAttackActive={liveAttackActive}
          query={query}
          setQuery={setQuery}
          onAlertClick={handleAlertClick}
          onChatSubmit={handleChatSubmit}
        />

        {(isChatting || chatResponse) && (
          <div className="relative overflow-hidden rounded-xl border border-cyan-500/50 bg-slate-900 p-5 shadow-neonCyan">
            <button
              onClick={() => {
                setChatResponse("");
                setIsChatting(false);
              }}
              className="absolute right-4 top-4 text-slate-400 hover:text-white"
              aria-label="Close Chat"
            >
              <X className="h-5 w-5" />
            </button>
            <div className="mb-3 flex items-center gap-2">
              <Bot className="h-5 w-5 text-cyan-400" />
              <h3 className="text-sm font-bold uppercase tracking-widest text-cyan-200">
                AI Log Analysis {chatSource && `[${chatSource}]`}
              </h3>
            </div>
            {isChatting ? (
              <div className="flex items-center gap-2 text-sm text-cyan-300/80">
                <Loader2 className="h-4 w-4 animate-spin" />
                Querying Neural Threat Engine...
              </div>
            ) : (
              <div className="prose prose-invert max-w-none text-sm">
                <p className="font-mono text-slate-100 whitespace-pre-wrap">{chatResponse}</p>
              </div>
            )}
          </div>
        )}

        <nav className="flex gap-2 border-b border-slate-800 pb-2">
          <NavLink
            to="/dashboard"
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-lg px-4 py-2 font-mono text-sm font-bold transition-all ${
                isActive
                  ? "bg-cyan-500/10 text-cyan-300 shadow-[inset_0_-2px_0_rgba(34,211,238,1)]"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`
            }
          >
            <Globe className="h-4 w-4" />
            Threat Dashboard
          </NavLink>
          <NavLink
            to="/telemetry"
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-lg px-4 py-2 font-mono text-sm font-bold transition-all ${
                isActive
                  ? "bg-cyan-500/10 text-cyan-300 shadow-[inset_0_-2px_0_rgba(34,211,238,1)]"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`
            }
          >
            <Activity className="h-4 w-4" />
            Live Ops & Telemetry
          </NavLink>
          <NavLink
            to="/intel"
            className={({ isActive }) =>
              `flex items-center gap-2 rounded-lg px-4 py-2 font-mono text-sm font-bold transition-all ${
                isActive
                  ? "bg-cyan-500/10 text-cyan-300 shadow-[inset_0_-2px_0_rgba(34,211,238,1)]"
                  : "text-slate-400 hover:bg-slate-800 hover:text-slate-200"
              }`
            }
          >
            <Database className="h-4 w-4" />
            Threat Intel Export
          </NavLink>
        </nav>

        <Routes>
          <Route
            path="/dashboard"
            element={
              <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <section className="grid gap-4 xl:grid-cols-[2.2fr_1fr]">
                  <NodeGraph
                    attackers={liveMapAttackers}
                    selectedId={selected.id}
                    onSelect={setSelectedAttackerId}
                  />
                  <TrafficTicker items={trafficTicker} />
                </section>
                <LiveAttackMap attackers={liveMapAttackers} liveAttackActive={liveAttackActive} />
                <AttackerProfile attacker={selected} />
              </div>
            }
          />
          <Route
            path="/telemetry"
            element={
              <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <SwarmControl nodes={swarmNodes} onInspectCompromised={handleOpenTelemetryFromSwarm} />
                <ThreatTelemetryFlow node4OpenSignal={telemetryNode4Signal} />
              </div>
            }
          />
          <Route
            path="/intel"
            element={
              <div className="flex flex-col gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                <ThreatIntelligenceExport threatReportReady={threatReportReady} compromisedNode={compromisedNode} />
              </div>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </div>
    </main>
  );
}

export default App;
