import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL ?? "http://api:8000";
const secureCookies = process.env.COOKIE_SECURE === "true";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const store = await cookies();
  const token = store.get("access_token")?.value;
  if (!token) return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  const target = new URL(`${API_URL}/api/v1/management/${path.join("/")}`);
  request.nextUrl.searchParams.forEach((value, key) => target.searchParams.append(key, value));
  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.text();
  let upstream = await fetch(target, {
    method: request.method,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": request.headers.get("content-type") ?? "application/json" },
    body,
    cache: "no-store",
  });
  let refreshed: { access_token: string; refresh_token: string; expires_in: number } | null = null;
  if (upstream.status === 401 && store.get("refresh_token")?.value) {
    const refresh = await fetch(`${API_URL}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: store.get("refresh_token")!.value }),
      cache: "no-store",
    });
    if (refresh.ok) {
      refreshed = await refresh.json();
      upstream = await fetch(target, {
        method: request.method,
        headers: { Authorization: `Bearer ${refreshed!.access_token}`, "Content-Type": request.headers.get("content-type") ?? "application/json" },
        body,
        cache: "no-store",
      });
    }
  }
  const response = new NextResponse(upstream.body, { status: upstream.status, headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json", "Content-Disposition": upstream.headers.get("content-disposition") ?? "" } });
  if (refreshed) {
    response.cookies.set("access_token", refreshed.access_token, { httpOnly: true, sameSite: "lax", secure: secureCookies, maxAge: refreshed.expires_in, path: "/" });
    response.cookies.set("refresh_token", refreshed.refresh_token, { httpOnly: true, sameSite: "strict", secure: secureCookies, maxAge: 7 * 86400, path: "/" });
  }
  return response;
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;
