"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";

export function LiveListener() {
  const client = useQueryClient();
  useEffect(() => {
    const stream = new EventSource("/api/management/stream/events");
    stream.addEventListener("telemetry", () => {
      client.invalidateQueries({ queryKey: ["overview"] });
      client.invalidateQueries({ queryKey: ["events"] });
      client.invalidateQueries({ queryKey: ["incidents"] });
      client.invalidateQueries({ queryKey: ["alerts"] });
    });
    return () => stream.close();
  }, [client]);
  return null;
}

