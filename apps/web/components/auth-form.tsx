"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const response = await fetch(`/api/auth/${mode}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => ({ detail: "Request failed" }));
      setError(body.detail ?? "Request failed");
      setLoading(false);
      return;
    }
    if (mode === "register") {
      const login = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: form.get("email"), password: form.get("password") }),
      });
      if (!login.ok) {
        router.push("/login");
        return;
      }
    }
    router.push("/dashboard");
    router.refresh();
  }

  return (
    <Card className="w-full max-w-md p-8">
      <p className="text-xs font-bold uppercase tracking-[0.3em] text-cyan-400">HoneyPot System</p>
      <h1 className="mt-3 text-3xl font-semibold">{mode === "login" ? "Analyst sign in" : "Create account"}</h1>
      <p className="mt-2 text-sm text-slate-400">Access the protected security operations workspace.</p>
      <form className="mt-8 space-y-4" onSubmit={submit}>
        <label className="block text-sm text-slate-300">Email
          <input name="email" type="email" required autoComplete="email" className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 outline-none focus:border-cyan-400" />
        </label>
        <label className="block text-sm text-slate-300">Password
          <input name="password" type="password" required minLength={mode === "register" ? 12 : 1} autoComplete={mode === "login" ? "current-password" : "new-password"} className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 outline-none focus:border-cyan-400" />
        </label>
        {error && <p role="alert" className="text-sm text-rose-300">{error}</p>}
        <Button className="w-full" disabled={loading}>{loading ? "Please wait…" : mode === "login" ? "Sign in" : "Register"}</Button>
      </form>
      <p className="mt-6 text-sm text-slate-400">
        {mode === "login" ? "Need an account? " : "Already registered? "}
        <Link className="text-cyan-300 hover:underline" href={mode === "login" ? "/register" : "/login"}>{mode === "login" ? "Register" : "Sign in"}</Link>
      </p>
    </Card>
  );
}

