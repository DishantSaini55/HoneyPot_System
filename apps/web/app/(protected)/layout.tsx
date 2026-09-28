import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { LiveListener } from "@/components/live-listener";

export default async function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const store = await cookies();
  if (!store.has("access_token") && !store.has("refresh_token")) redirect("/login");
  return <AppShell><LiveListener />{children}</AppShell>;
}
