import { cookies } from "next/headers";
import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.API_URL ?? "http://api:8000";

async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const token = (await cookies()).get("access_token")?.value;
  if (!token) return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  const target = new URL(`${API_URL}/api/v1/management/${path.join("/")}`);
  request.nextUrl.searchParams.forEach((value, key) => target.searchParams.append(key, value));
  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.text();
  const upstream = await fetch(target, {
    method: request.method,
    headers: { Authorization: `Bearer ${token}`, "Content-Type": request.headers.get("content-type") ?? "application/json" },
    body,
    cache: "no-store",
  });
  return new NextResponse(upstream.body, { status: upstream.status, headers: { "Content-Type": upstream.headers.get("content-type") ?? "application/json", "Content-Disposition": upstream.headers.get("content-disposition") ?? "" } });
}

export const GET = proxy;
export const POST = proxy;
export const PATCH = proxy;

