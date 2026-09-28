"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import type { EventRecord, Incident, Page, Severity } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function IncidentsView() {
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: () => api<Page<Incident>>("incidents?page_size=100") });
  return <Card>{incidents.data?.items.length === 0 ? <EmptyState title="No incidents" detail="An incident is created only when a real detection rule triggers." /> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs uppercase text-slate-500"><tr><th className="py-2">Incident</th><th>Source</th><th>Attack type</th><th>Last seen</th><th>Status</th><th>Severity</th><th>Risk</th></tr></thead><tbody>{incidents.data?.items.map((item) => <tr key={item.id} className="border-t border-slate-800"><td className="py-3"><Link href={`/incidents/${item.id}`} className="font-mono text-cyan-300">INC-{String(item.incident_number).padStart(6, "0")}</Link></td><td className="font-mono">{item.source_ip}</td><td>{item.attack_type}</td><td>{formatDate(item.last_seen_at)}</td><td><Badge>{item.status}</Badge></td><td><Badge>{item.severity}</Badge></td><td>{item.risk_score}</td></tr>)}</tbody></table></div>}</Card>;
}

interface Prediction {
  model_version: string;
  classification: string;
  confidence: number;
  features: Record<string, number>;
}

interface Assignee {
  id: string;
  email: string;
  role: string;
}

export function IncidentDetail({ id }: { id: string }) {
  const queryClient = useQueryClient();
  const detail = useQuery({ queryKey: ["incident", id], queryFn: () => api<{ incident: Incident; events: EventRecord[]; ml_predictions: Prediction[] }>(`incidents/${id}`) });
  const assignees = useQuery({ queryKey: ["assignees"], queryFn: () => api<Assignee[]>("users/assignees"), retry: false });
  const [note, setNote] = useState<string | null>(null);
  const [severity, setSeverity] = useState<Severity | null>(null);
  const [assignedTo, setAssignedTo] = useState<string | null>(null);
  const [question, setQuestion] = useState("Why is this incident suspicious?");
  const [analysis, setAnalysis] = useState("");

  const update = useMutation({
    mutationFn: (changes: Record<string, unknown>) => api<Incident>(`incidents/${id}`, { method: "PATCH", body: JSON.stringify(changes) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["incident", id] });
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
    },
  });
  const ask = useMutation({
    mutationFn: () => api<{ answer: string }>(`incidents/${id}/analysis`, { method: "POST", body: JSON.stringify({ question }) }),
    onSuccess: (result) => setAnalysis(result.answer),
  });

  if (!detail.data) return <p>Loading incident...</p>;
  const { incident, events, ml_predictions } = detail.data;
  const formNote = note ?? incident.note ?? "";
  const formSeverity = severity ?? incident.severity;
  const formAssignee = assignedTo ?? incident.assigned_to_id ?? "";
  const latestPrediction = ml_predictions[0];
  return <div className="space-y-5">
    <Card>
      <div className="flex flex-wrap items-start justify-between gap-4"><div><CardTitle>INC-{String(incident.incident_number).padStart(6, "0")}</CardTitle><p className="mt-2 font-mono text-cyan-300">{incident.source_ip}</p><p className="mt-2 text-sm text-slate-400">{incident.attack_type}</p></div><div className="flex items-center gap-2"><Badge>{incident.severity}</Badge><Badge>{incident.status}</Badge><span className="text-2xl font-semibold">{incident.risk_score}</span></div></div>
      <div className="mt-5 flex flex-wrap gap-2"><Button onClick={() => update.mutate({ status: "ACKNOWLEDGED" })} disabled={incident.status === "ACKNOWLEDGED"}>Acknowledge</Button><Button className="bg-emerald-400 hover:bg-emerald-300" onClick={() => update.mutate({ status: "RESOLVED" })}>Resolve</Button><Button className="bg-slate-700 text-white hover:bg-slate-600" onClick={() => update.mutate({ status: "NEW" })}>Reopen</Button></div>
    </Card>
    <div className="grid gap-5 xl:grid-cols-2">
      <Card><CardTitle>Investigation fields</CardTitle><div className="mt-4 space-y-3"><label className="block text-sm">Severity<select value={formSeverity} onChange={(event) => setSeverity(event.target.value as Severity)} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 p-2">{["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((value) => <option key={value}>{value}</option>)}</select></label><label className="block text-sm">Assignee<select value={formAssignee} onChange={(event) => setAssignedTo(event.target.value)} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 p-2"><option value="">Unassigned</option>{assignees.data?.map((user) => <option key={user.id} value={user.id}>{user.email} ({user.role})</option>)}</select></label><label className="block text-sm">Analyst note<textarea value={formNote} onChange={(event) => setNote(event.target.value)} rows={5} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 p-2" /></label><Button onClick={() => update.mutate({ severity: formSeverity, assigned_to_id: formAssignee || null, note: formNote })}>Save investigation</Button></div></Card>
      <Card><CardTitle>ML classification</CardTitle>{latestPrediction ? <div className="mt-4"><p className="text-2xl font-semibold">{latestPrediction.classification}</p><p className="mt-1 text-sm text-slate-400">Confidence {(latestPrediction.confidence * 100).toFixed(1)}% from {latestPrediction.model_version}</p><pre className="mt-4 overflow-auto text-xs text-slate-400">{JSON.stringify(latestPrediction.features, null, 2)}</pre></div> : <p className="mt-4 text-sm text-slate-400">No model prediction is available.</p>}</Card>
    </div>
    <Card><CardTitle>AI analyst (optional)</CardTitle><div className="mt-4 flex gap-2"><input value={question} onChange={(event) => setQuestion(event.target.value)} className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3" /><Button onClick={() => ask.mutate()}>Analyze</Button></div>{ask.error && <p className="mt-3 text-sm text-amber-300">AI analyst is unavailable or not configured.</p>}{analysis && <div className="mt-4 rounded-lg border border-cyan-400/20 bg-cyan-400/5 p-4"><p className="text-xs font-semibold uppercase text-cyan-300">AI-generated analysis</p><p className="mt-2 whitespace-pre-wrap text-sm text-slate-300">{analysis}</p></div>}</Card>
    <Card><CardTitle>Correlated timeline</CardTitle><ol className="mt-5 space-y-4 border-l border-slate-700 pl-5">{events.map((event) => <li key={event.id} className="relative"><span className="absolute -left-[25px] top-1 size-2 rounded-full bg-cyan-400" /><p className="text-xs text-slate-500">{formatDate(event.timestamp)}</p><Link href={`/events/${event.id}`} className="font-medium text-slate-200 hover:text-cyan-300">{event.event_type} · {event.protocol}</Link><p className="font-mono text-sm text-slate-400">{event.command ?? event.detections.map((d) => d.attack_type).join(", ")}</p></li>)}</ol></Card>
  </div>;
}
