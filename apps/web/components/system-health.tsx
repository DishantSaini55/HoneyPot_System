"use client";

import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";

type Health = Record<string, { status: string; error?: string }>;
export function SystemHealth() {
  const health = useQuery({ queryKey: ["health"], queryFn: async () => { const r = await fetch("/api/health/all", { cache: "no-store" }); if (!r.ok) throw new Error(); return r.json() as Promise<Health>; }, refetchInterval: 10_000 });
  if (!health.data) return <p>Checking services…</p>;
  return <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{Object.entries(health.data).map(([name, value]) => <Card key={name}><div className="flex items-center justify-between"><p className="capitalize">{name}</p><span className={`size-3 rounded-full ${value.status === "healthy" ? "bg-emerald-400" : "bg-rose-400"}`} /></div><p className="mt-2 text-sm capitalize text-slate-400">{value.status}</p>{value.error && <p className="mt-1 text-xs text-rose-300">{value.error}</p>}</Card>)}</div>;
}

