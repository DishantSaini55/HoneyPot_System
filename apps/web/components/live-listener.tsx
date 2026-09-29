"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";

export function LiveListener() {
  const client = useQueryClient();
  const [status, setStatus] = useState<"connecting" | "live" | "reconnecting">("connecting");
  const [attempt, setAttempt] = useState(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    const stream = new EventSource("/api/management/stream/events");
    stream.onopen = () => setStatus("live");
    stream.addEventListener("telemetry", () => {
      client.invalidateQueries({ queryKey: ["overview"] });
      client.invalidateQueries({ queryKey: ["events"] });
      client.invalidateQueries({ queryKey: ["incidents"] });
      client.invalidateQueries({ queryKey: ["alerts"] });
    });
    stream.onerror = () => {
      stream.close();
      setStatus("reconnecting");
      if (!timerRef.current) timerRef.current = setTimeout(() => {
        timerRef.current = null;
        setAttempt((value) => value + 1);
      }, 1_000);
    };
    return () => stream.close();
  }, [attempt, client]);
  return <div role="status" aria-live="polite" className="mb-3 text-xs text-slate-500">Live telemetry: <span className={status === "live" ? "text-emerald-400" : "text-amber-300"}>{status === "live" ? "connected" : status}</span>{status !== "live" && <button type="button" onClick={() => { setStatus("connecting"); setAttempt((value) => value + 1); }} className="ml-2 text-cyan-300 hover:underline">Reconnect</button>}</div>;
}
