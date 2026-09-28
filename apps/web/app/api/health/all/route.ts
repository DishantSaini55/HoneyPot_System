import { NextResponse } from "next/server";
const API_URL = process.env.API_URL ?? "http://api:8000";
export async function GET() {
  const names = ["", "/database", "/redis", "/workers", "/honeypots"];
  const results = await Promise.all(names.map(async (path) => { try { const response = await fetch(`${API_URL}/health${path}`, { cache: "no-store" }); return await response.json(); } catch { return { status: "unhealthy", error: "unreachable" }; } }));
  return NextResponse.json({ api: results[0], database: results[1], redis: results[2], worker: results[3], honeypots: results[4] });
}

