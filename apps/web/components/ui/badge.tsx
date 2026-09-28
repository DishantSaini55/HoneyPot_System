import type { ComponentProps } from "react";
import { cn } from "@/lib/utils";

const colors: Record<string, string> = {
  LOW: "border-sky-500/30 bg-sky-500/10 text-sky-300",
  MEDIUM: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  HIGH: "border-orange-500/30 bg-orange-500/10 text-orange-300",
  CRITICAL: "border-rose-500/40 bg-rose-500/10 text-rose-300",
  NEW: "border-rose-500/40 bg-rose-500/10 text-rose-300",
  ACKNOWLEDGED: "border-amber-500/30 bg-amber-500/10 text-amber-300",
  RESOLVED: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
};

export function Badge({ className, children, ...props }: ComponentProps<"span">) {
  const value = String(children);
  return <span className={cn("inline-flex rounded-full border px-2 py-0.5 text-xs font-semibold", colors[value], className)} {...props}>{children}</span>;
}

