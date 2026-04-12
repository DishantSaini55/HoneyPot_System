import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer } from "react-leaflet";

function nowTime() {
  return new Date().toLocaleTimeString([], { hour12: false });
}

function LiveAttackMap({ attackers, liveAttackActive }) {
  const [activeAttackId, setActiveAttackId] = useState(attackers[0]?.id ?? null);
  const [pulseOn, setPulseOn] = useState(true);
  const [eventFeed, setEventFeed] = useState([]);

  useEffect(() => {
    if (!attackers.length) {
      return undefined;
    }

    const tick = window.setInterval(() => {
      // Force selection of the live hacker if active for the demo
      const next = liveAttackActive 
        ? attackers.find(a => a.id.startsWith("LIVE_")) 
        : attackers[Math.floor(Math.random() * attackers.length)];
      
      if (next) {
        setActiveAttackId(next.id);
        setEventFeed((prev) => {
          const entry = `${nowTime()} | ${next.alias} -> ${next.targetNode} | ${next.weapon}`;
          return [entry, ...prev].slice(0, 6);
        });
      }
    }, 1600);

    return () => window.clearInterval(tick);
  }, [attackers, liveAttackActive]);

  useEffect(() => {
    const pulseTimer = window.setInterval(() => {
      setPulseOn((prev) => !prev);
    }, 420);

    return () => window.clearInterval(pulseTimer);
  }, []);

  const mapCenter = useMemo(() => [20.5937, 0], []);

  return (
    <section className="rounded-xl border border-slate-800 bg-panel/90 p-4">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-slateText">Live Attack Map</p>
          <h2 className="text-xl font-bold text-cyan-100">Global Strike Surface</h2>
        </div>
        <span className="rounded border border-neonRed/70 bg-neonRed/10 px-2 py-1 font-mono text-xs text-neonRed">
          Real-Time Feed
        </span>
      </div>

      <div className="grid gap-4 lg:grid-cols-[2fr_1fr]">
        <div className="overflow-hidden rounded-lg border border-slate-700/60">
          <MapContainer
            center={mapCenter}
            zoom={2}
            minZoom={2}
            scrollWheelZoom={false}
            className="h-[320px] w-full"
            worldCopyJump
          >
            <TileLayer
              attribution='&copy; OpenStreetMap contributors &copy; CARTO'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />

            {attackers.map((attacker) => {
              const isActive = attacker.id === activeAttackId;
              const radius = isActive ? (pulseOn ? 14 : 8) : 6;
              const fillOpacity = isActive ? (pulseOn ? 0.95 : 0.35) : 0.3;

              return (
                <CircleMarker
                  key={attacker.id}
                  center={[attacker.coordinates.lat, attacker.coordinates.lng]}
                  pathOptions={{
                    color: attacker.id.startsWith("LIVE_") ? "#00ffff" : "#ff3d5f",
                    fillColor: attacker.id.startsWith("LIVE_") ? "#00ffff" : "#ff3d5f",
                    fillOpacity,
                    weight: isActive ? 2 : 1,
                  }}
                  radius={attacker.id.startsWith("LIVE_") && isActive ? 20 : radius}
                >
                  <Popup>
                    <div className="font-mono text-xs">
                      <p>{attacker.alias}</p>
                      <p>{attacker.sourceIp}</p>
                      <p>{attacker.classification}</p>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}
          </MapContainer>
        </div>

        <div className="rounded-lg border border-slate-700 bg-slate-900/70 p-3">
          <p className="mb-2 text-xs uppercase tracking-[0.2em] text-slateText">Attack Pulse Log</p>
          <div className="space-y-2">
            {eventFeed.length === 0 ? (
              <p className="font-mono text-xs text-slate-500">Initializing telemetry stream...</p>
            ) : (
              eventFeed.map((event) => (
                <p key={event} className="rounded border border-slate-700 bg-slate-950/70 px-2 py-1 font-mono text-xs text-red-200">
                  {event}
                </p>
              ))
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

export default LiveAttackMap;
