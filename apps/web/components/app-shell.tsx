"use client";

import { Activity, Bell, ChartNoAxesCombined, Crosshair, Database, FileClock, ListChecks, LogOut, Radar, ScrollText, Server, Settings, ShieldAlert, Users } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

const navigation = [
  ["/dashboard", "Overview", Activity],
  ["/events", "Events", Database],
  ["/incidents", "Incidents", ShieldAlert],
  ["/attackers", "Attackers", Crosshair],
  ["/sessions", "Sessions", FileClock],
  ["/honeypots", "Honeypots", Server],
  ["/analytics", "Analytics", ChartNoAxesCombined],
  ["/alerts", "Alerts", Bell],
  ["/threat-intelligence", "Threat Intel", Radar],
  ["/admin/users", "Users", Users],
  ["/admin/rules", "Alert rules", ListChecks],
  ["/admin/audit-logs", "Audit logs", ScrollText],
  ["/settings", "Settings", Settings],
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  async function logout() {
    await fetch("/api/auth/logout", { method: "POST" });
    router.push("/login");
    router.refresh();
  }
  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[250px_1fr]">
      <aside className="border-b border-slate-800 bg-slate-950/90 p-5 lg:min-h-screen lg:border-b-0 lg:border-r">
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-xl bg-cyan-400 text-slate-950"><Radar className="size-5" /></div>
          <div><p className="font-semibold">HoneyPot SOC</p><p className="text-xs text-slate-500">Management plane</p></div>
        </div>
        <nav aria-label="Primary" className="mt-8 grid grid-cols-2 gap-1 sm:grid-cols-3 lg:grid-cols-1">
          {navigation.map(([href, label, Icon]) => (
            <Link key={href} href={href} className={cn("flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-slate-900 hover:text-slate-100", pathname === href || (href !== "/dashboard" && pathname.startsWith(`${href}/`)) ? "bg-cyan-400/10 text-cyan-300" : "")}>
              <Icon className="size-4" />{label}
            </Link>
          ))}
        </nav>
        <button onClick={logout} className="mt-8 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 hover:bg-slate-900 hover:text-slate-100"><LogOut className="size-4" />Sign out</button>
      </aside>
      <main className="min-w-0 p-5 lg:p-8">{children}</main>
    </div>
  );
}
