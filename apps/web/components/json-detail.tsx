"use client";

import { useQuery } from "@tanstack/react-query";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";

export function JsonDetail({ endpoint, queryKey }: { endpoint: string; queryKey: string }) {
  const result = useQuery({ queryKey: [queryKey], queryFn: () => api<Record<string, unknown>>(endpoint) });
  if (!result.data) return <p className="text-slate-400">Loading…</p>;
  return <Card><pre className="max-h-[70vh] overflow-auto text-sm text-slate-300">{JSON.stringify(result.data, null, 2)}</pre></Card>;
}

