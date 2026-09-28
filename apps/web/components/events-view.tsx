"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import type { EventRecord, Page } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function EventsView() {
  const [search, setSearch] = useState("");
  const [severity, setSeverity] = useState("");
  const [attackType, setAttackType] = useState("");
  const [honeypot, setHoneypot] = useState("");
  const [endpoint, setEndpoint] = useState("");
  const [country, setCountry] = useState("");
  const query = new URLSearchParams({ page_size: "100" });
  if (search) query.set("search", search);
  if (severity) query.set("severity", severity);
  if (attackType) query.set("attack_type", attackType);
  if (honeypot) query.set("honeypot", honeypot);
  if (endpoint) query.set("endpoint", endpoint);
  if (country) query.set("country", country);
  const events = useQuery({ queryKey: ["events", search, severity, attackType, honeypot, endpoint, country], queryFn: () => api<Page<EventRecord>>(`events?${query}`) });
  return <Card><div className="mb-5 grid gap-3 md:grid-cols-2 xl:grid-cols-3"><input aria-label="Search events" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="IP, session, event ID, or command" className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2" /><input aria-label="Filter by attack type" value={attackType} onChange={(e) => setAttackType(e.target.value)} placeholder="Attack type" className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2" /><input aria-label="Filter by endpoint" value={endpoint} onChange={(e) => setEndpoint(e.target.value)} placeholder="HTTP endpoint" className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2" /><input aria-label="Filter by country" value={country} maxLength={2} onChange={(e) => setCountry(e.target.value)} placeholder="Country code" className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2" /><select aria-label="Filter by severity" value={severity} onChange={(e) => setSeverity(e.target.value)} className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"><option value="">All severities</option>{["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((value) => <option key={value}>{value}</option>)}</select><select aria-label="Filter by honeypot" value={honeypot} onChange={(e) => setHoneypot(e.target.value)} className="rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"><option value="">All honeypots</option><option>SSH</option><option>HTTP</option></select></div>
    {events.data?.items.length === 0 ? <EmptyState /> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Timestamp</th><th>Source</th><th>Protocol</th><th>Type</th><th>Detection</th><th>Severity</th><th>Risk</th></tr></thead><tbody>{events.data?.items.map((item) => <tr key={item.id} className="border-t border-slate-800"><td className="whitespace-nowrap py-3 text-slate-400">{formatDate(item.timestamp)}</td><td className="font-mono">{item.source_ip}</td><td>{item.protocol}</td><td><Link href={`/events/${item.id}`} className="text-cyan-300 hover:underline">{item.event_type}</Link></td><td>{item.detections.map((d) => d.attack_type).join(", ") || "—"}</td><td><Badge>{item.severity}</Badge></td><td>{item.risk_score}</td></tr>)}</tbody></table></div>}
  </Card>;
}
