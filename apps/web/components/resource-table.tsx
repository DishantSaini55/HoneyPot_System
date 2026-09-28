"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { EmptyState } from "@/components/ui/empty-state";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

type Row = Record<string, unknown>;

function renderValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "Unavailable";
  if (typeof value === "object") return JSON.stringify(value);
  if (typeof value === "string" && /^\d{4}-\d{2}-\d{2}T/.test(value)) return formatDate(value);
  return String(value);
}

export function ResourceTable({ endpoint, queryKey, columns, link }: { endpoint: string; queryKey: string; columns: [string, string][]; link?: (row: Row) => string }) {
  const result = useQuery({ queryKey: [queryKey], queryFn: () => api<Row[] | { items: Row[] }>(endpoint) });
  const rows = Array.isArray(result.data) ? result.data : result.data?.items ?? [];
  if (result.isLoading) return <p className="text-slate-400">Loading…</p>;
  if (result.error) return <p role="alert" className="text-rose-300">Unable to load this resource. Your role may not have access.</p>;
  return <Card>{rows.length === 0 ? <EmptyState /> : <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="text-xs uppercase text-slate-500"><tr>{columns.map(([key, label]) => <th key={key} className="py-2 pr-5">{label}</th>)}</tr></thead><tbody>{rows.map((row, index) => <tr key={String(row.id ?? row.source_ip ?? index)} className="border-t border-slate-800">{columns.map(([key], columnIndex) => <td key={key} className="max-w-sm py-3 pr-5"><span className="line-clamp-2">{columnIndex === 0 && link ? <Link className="font-mono text-cyan-300 hover:underline" href={link(row)}>{renderValue(row[key])}</Link> : renderValue(row[key])}</span></td>)}</tr>)}</tbody></table></div>}</Card>;
}

