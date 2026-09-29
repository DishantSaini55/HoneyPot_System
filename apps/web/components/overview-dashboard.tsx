"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import type { AttackMapData, EventRecord, Overview, Page } from "@/lib/types";

const pieColors = ["#38bdf8", "#fbbf24", "#fb923c", "#fb7185"];

export function OverviewDashboard() {
  const overview = useQuery({ queryKey: ["overview"], queryFn: () => api<Overview>("analytics/overview") });
  const events = useQuery({ queryKey: ["events", "latest"], queryFn: () => api<Page<EventRecord>>("events?page_size=8") });
  const map = useQuery({ queryKey: ["attack-map"], queryFn: () => api<AttackMapData>("attackers-map") });
  if (overview.isLoading) return <p className="text-slate-400">Loading telemetry…</p>;
  if (overview.error) return <Card><p role="alert" className="text-rose-300">Unable to load the management API. Check service health and retry.</p><button type="button" onClick={() => overview.refetch()} className="mt-3 text-sm text-cyan-300 hover:underline">Retry request</button></Card>;
  const data = overview.data!;
  const cards = [
    ["Total events", data.total_events], ["Active sessions", data.active_sessions], ["Unique attackers", data.unique_attackers],
    ["Critical incidents", data.critical_incidents], ["Detections", data.detection_count], ["Open alerts", data.alert_count],
    ["Auth failures", data.authentication_failures], ["Detection rate", data.detection_rate === null ? "N/A" : `${(data.detection_rate * 100).toFixed(1)}%`],
  ];
  const severity = Object.entries(data.severity).map(([name, value]) => ({ name, value }));
  const categories = Object.entries(data.categories).map(([name, value]) => ({ name, value }));
  return (
    <div className="space-y-5">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{cards.map(([label, value]) => <Card key={label}><p className="text-xs uppercase tracking-wider text-slate-500">{label}</p><p className="mt-3 text-3xl font-semibold">{value}</p></Card>)}</div>
      {data.total_events === 0 ? <EmptyState /> : <>
        <div className="grid gap-5 xl:grid-cols-2">
          <Card><CardTitle>Detection categories</CardTitle><div className="mt-5 h-64"><ResponsiveContainer width="100%" height="100%"><BarChart data={categories}><CartesianGrid stroke="#1e293b" vertical={false} /><XAxis dataKey="name" stroke="#64748b" tick={{ fontSize: 10 }} /><YAxis allowDecimals={false} stroke="#64748b" /><Tooltip contentStyle={{ background: "#020617", border: "1px solid #334155" }} /><Bar dataKey="value" fill="#22d3ee" radius={[6, 6, 0, 0]} /></BarChart></ResponsiveContainer></div></Card>
          <Card><CardTitle>Severity distribution</CardTitle><div className="mt-5 h-64"><ResponsiveContainer width="100%" height="100%"><PieChart><Pie data={severity} dataKey="value" nameKey="name" innerRadius={55} outerRadius={90}>{severity.map((entry, index) => <Cell key={entry.name} fill={pieColors[index % pieColors.length]} />)}</Pie><Tooltip contentStyle={{ background: "#020617", border: "1px solid #334155" }} /></PieChart></ResponsiveContainer></div></Card>
        </div>
        <div className="grid gap-5 xl:grid-cols-2">
          <Card><CardTitle>Attack timeline</CardTitle><div className="mt-5 h-64"><ResponsiveContainer width="100%" height="100%"><AreaChart data={data.timeline}><CartesianGrid stroke="#1e293b" vertical={false} /><XAxis dataKey="bucket" stroke="#64748b" tick={{ fontSize: 10 }} /><YAxis allowDecimals={false} stroke="#64748b" /><Tooltip contentStyle={{ background: "#020617", border: "1px solid #334155" }} /><Area type="monotone" dataKey="count" stroke="#22d3ee" fill="#22d3ee33" /></AreaChart></ResponsiveContainer></div></Card>
          <Card><CardTitle>Attack map</CardTitle><div className="relative mt-5 h-64 overflow-hidden rounded-lg border border-slate-800 bg-slate-950" role="img" aria-label="Geographic attack source plot"><div className="absolute inset-0 opacity-30" style={{ backgroundImage: "linear-gradient(#334155 1px, transparent 1px), linear-gradient(90deg, #334155 1px, transparent 1px)", backgroundSize: "12.5% 25%" }} />{map.data?.points.map((point) => <span key={point.source_ip} title={`${point.source_ip} - ${point.city ?? point.country ?? "location"}`} className="absolute size-3 -translate-x-1/2 -translate-y-1/2 rounded-full bg-rose-400 shadow-[0_0_14px_#fb7185]" style={{ left: `${((point.longitude + 180) / 360) * 100}%`, top: `${((90 - point.latitude) / 180) * 100}%` }} />)}<p className="absolute bottom-3 left-3 text-xs text-slate-400">{map.data?.points.length ? `${map.data.points.length} located sources` : "Location unavailable"}{map.data?.unavailable_count ? ` - ${map.data.unavailable_count} sources unavailable` : ""}</p></div></Card>
        </div>
        <div className="grid gap-5 lg:grid-cols-3">
          <Card><CardTitle>Top attackers</CardTitle><ol className="mt-4 space-y-2 text-sm">{data.top_attackers.map((item) => <li key={item.source_ip} className="flex justify-between"><Link href={`/attackers/${item.source_ip}`} className="font-mono text-cyan-300">{item.source_ip}</Link><span>{item.count}</span></li>)}</ol></Card>
          <Card><CardTitle>Targeted endpoints</CardTitle><ol className="mt-4 space-y-2 text-sm">{data.top_targeted_endpoints.map((item) => <li key={item.path} className="flex gap-3"><span className="min-w-0 flex-1 truncate font-mono text-slate-300">{item.path}</span><span>{item.count}</span></li>)}</ol></Card>
          <Card><CardTitle>Top commands</CardTitle><ol className="mt-4 space-y-2 text-sm">{data.top_commands.map((item) => <li key={item.command} className="flex gap-3"><span className="min-w-0 flex-1 truncate font-mono text-slate-300">{item.command}</span><span>{item.count}</span></li>)}</ol></Card>
        </div>
        <Card><div className="flex items-center justify-between"><CardTitle>Live events</CardTitle><Link href="/events" className="text-sm text-cyan-300">View all</Link></div><div className="mt-4 overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Time</th><th>Source</th><th>Protocol</th><th>Event</th><th>Severity</th><th>Risk</th></tr></thead><tbody>{events.data?.items.map((event) => <tr key={event.id} className="border-t border-slate-800"><td className="py-3 text-slate-400">{formatDate(event.timestamp)}</td><td><Link className="font-mono text-cyan-300" href={`/attackers/${event.source_ip}`}>{event.source_ip}</Link></td><td>{event.protocol}</td><td><Link href={`/events/${event.id}`} className="hover:text-cyan-300">{event.event_type}</Link></td><td><Badge>{event.severity}</Badge></td><td>{event.risk_score}</td></tr>)}</tbody></table></div></Card>
      </>}
    </div>
  );
}
