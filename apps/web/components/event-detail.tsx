"use client";

import { useQuery } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Card, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { EventRecord } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function EventDetail({ id }: { id: string }) {
  const event = useQuery({ queryKey: ["event", id], queryFn: () => api<EventRecord>(`events/${id}`) });
  if (!event.data) return <p className="text-slate-400">Loading event…</p>;
  const item = event.data;
  return <div className="grid gap-5 xl:grid-cols-2"><Card><CardTitle>Event metadata</CardTitle><dl className="mt-5 grid grid-cols-[150px_1fr] gap-3 text-sm"><dt className="text-slate-500">Event ID</dt><dd className="break-all font-mono">{item.id}</dd><dt className="text-slate-500">Timestamp</dt><dd>{formatDate(item.timestamp)}</dd><dt className="text-slate-500">Source</dt><dd className="font-mono">{item.source_ip}:{item.source_port ?? "—"}</dd><dt className="text-slate-500">Destination</dt><dd>{item.protocol}/{item.destination_port}</dd><dt className="text-slate-500">Session</dt><dd className="break-all font-mono">{item.session_id}</dd><dt className="text-slate-500">Severity</dt><dd><Badge>{item.severity}</Badge> · Risk {item.risk_score}</dd><dt className="text-slate-500">Command</dt><dd className="break-all font-mono">{item.command ?? "—"}</dd></dl></Card><Card><CardTitle>Rule evidence</CardTitle><div className="mt-5 space-y-3">{item.detections.length ? item.detections.map((d) => <div key={`${d.rule_id}-${d.attack_type}`} className="rounded-xl border border-slate-800 p-4"><div className="flex justify-between"><p className="font-medium text-cyan-300">{d.attack_type}</p><span>+{d.score}</span></div><p className="mt-1 text-xs text-slate-500">{d.rule_id}</p><pre className="mt-3 overflow-auto text-xs text-slate-300">{JSON.stringify(d.evidence, null, 2)}</pre></div>) : <p className="text-slate-500">No detection rule triggered for this event.</p>}</div></Card><Card className="xl:col-span-2"><CardTitle>Captured payload</CardTitle><pre className="mt-4 max-h-96 overflow-auto rounded-xl bg-slate-950 p-4 text-xs text-slate-300">{JSON.stringify(item.payload, null, 2)}</pre></Card></div>;
}

