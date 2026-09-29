import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL ?? "http://api:8000";
const secureCookies = process.env.COOKIE_SECURE === "true";

export async function POST(request: NextRequest, context: { params: Promise<{ action: string }> }) {
  const { action } = await context.params;
  if (!["login", "register", "refresh", "logout"].includes(action)) {
    return NextResponse.json({ detail: "Not found" }, { status: 404 });
  }
  const store = await cookies();
  let body = await request.json().catch(() => ({}));
  if (action === "refresh" || action === "logout") body = { refresh_token: store.get("refresh_token")?.value };
  let upstream: globalThis.Response;
  try {
    upstream = await fetch(`${API_URL}/api/v1/auth/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      cache: "no-store",
      signal: AbortSignal.timeout(10_000),
    });
  } catch {
    return NextResponse.json({ detail: "Authentication service is unavailable. Try again later." }, { status: 503 });
  }
  const text = await upstream.text();
  const response = new NextResponse(text || null, { status: upstream.status, headers: { "Content-Type": "application/json" } });
  if (upstream.ok && ["login", "refresh"].includes(action)) {
    const tokens = JSON.parse(text);
    response.cookies.set("access_token", tokens.access_token, { httpOnly: true, sameSite: "lax", secure: secureCookies, maxAge: tokens.expires_in, path: "/" });
    response.cookies.set("refresh_token", tokens.refresh_token, { httpOnly: true, sameSite: "strict", secure: secureCookies, maxAge: 7 * 86400, path: "/" });
  }
  if (action === "logout") {
    response.cookies.delete("access_token");
    response.cookies.delete("refresh_token");
  }
  return response;
}
