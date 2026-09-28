"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import type { EventRecord, Incident, Page } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function IncidentsView() {
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: () => api<Page<Incident>>("incidents?page_size=100") });
  return <Card>{incidents.data?.items.length === 0 ? <EmptyState title="No incidents" detail="An incident is created only when a real detection rule triggers." /> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Incident</th><th>Source</th><th>Attack type</th><th>Last seen</th><th>Status</th><th>Severity</th><th>Risk</th></tr></thead><tbody>{incidents.data?.items.map((item) => <tr key={item.id} className="border-t border-slate-800"><td className="py-3"><Link href={`/incidents/${item.id}`} className="font-mono text-cyan-300">INC-{String(item.incident_number).padStart(6, "0")}</Link></td><td className="font-mono">{item.source_ip}</td><td>{item.attack_type}</td><td>{formatDate(item.last_seen_at)}</td><td><Badge>{item.status}</Badge></td><td><Badge>{item.severity}</Badge></td><td>{item.risk_score}</td></tr>)}</tbody></table></div>}</Card>;
}

export function IncidentDetail({ id }: { id: string }) {
  const queryClient = useQueryClient();
  const detail = useQuery({ queryKey: ["incident", id], queryFn: () => api<{ incident: Incident; events: EventRecord[] }>(`incidents/${id}`) });
  const update = useMutation({ mutationFn: (status: string) => api<Incident>(`incidents/${id}`, { method: "PATCH", body: JSON.stringify({ status }) }), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["incident", id] }); queryClient.invalidateQueries({ queryKey: ["incidents"] }); } });
  if (!detail.data) return <p>Loading incident…</p>;
  const { incident, events } = detail.data;
  return <div className="space-y-5"><Card><div className="flex flex-wrap items-start justify-between gap-4"><div><CardTitle>INC-{String(incident.incident_number).padStart(6, "0")}</CardTitle><p className="mt-2 font-mono text-cyan-300">{incident.source_ip}</p><p className="mt-2 text-sm text-slate-400">{incident.attack_type}</p></div><div className="flex items-center gap-2"><Badge>{incident.severity}</Badge><Badge>{incident.status}</Badge><span className="text-2xl font-semibold">{incident.risk_score}</span></div></div><div className="mt-5 flex flex-wrap gap-2"><Button onClick={() => update.mutate("ACKNOWLEDGED")} disabled={incident.status === "ACKNOWLEDGED"}>Acknowledge</Button><Button className="bg-emerald-400 hover:bg-emerald-300" onClick={() => update.mutate("RESOLVED")}>Resolve</Button><Button className="bg-slate-700 text-white hover:bg-slate-600" onClick={() => update.mutate("NEW")}>Reopen</Button></div></Card><Card><CardTitle>Correlated timeline</CardTitle><ol className="mt-5 space-y-4 border-l border-slate-700 pl-5">{events.map((event) => <li key={event.id} className="relative"><span className="absolute -left-[25px] top-1 size-2 rounded-full bg-cyan-400" /><p className="text-xs text-slate-500">{formatDate(event.timestamp)}</p><Link href={`/events/${event.id}`} className="font-medium text-slate-200 hover:text-cyan-300">{event.event_type} · {event.protocol}</Link><p className="font-mono text-sm text-slate-400">{event.command ?? event.detections.map((d) => d.attack_type).join(", ")}</p></li>)}</ol></Card></div>;
}

