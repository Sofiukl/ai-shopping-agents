"use client";

import { useEffect, useState } from "react";
import { CopilotKit } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

type Session = { threadId: string; name: string | null };

const STORAGE_KEY = "shop-session";

function loadSession(): Session {
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (saved) return JSON.parse(saved);
  } catch {}
  return { threadId: crypto.randomUUID(), name: null };
}

function saveSession(s: Session) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  } catch {}
}

function SignIn({ threadId, onSignedIn }: { threadId: string; onSignedIn: (name: string) => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      const resp = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ threadId, email, password }),
      });
      const body = await resp.json();
      if (!resp.ok) throw new Error(body.detail ?? "Sign-in failed");
      setPassword("");
      onSignedIn(body.user.name);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign-in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit} className="mx-auto mt-16 flex w-full max-w-sm flex-col gap-3">
      <h2 className="text-lg font-semibold">Sign in to start shopping</h2>
      <input
        className="rounded-md border px-3 py-2"
        type="email"
        placeholder="Email"
        autoComplete="username"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
      />
      <input
        className="rounded-md border px-3 py-2"
        type="password"
        placeholder="Password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      {error && <p className="text-sm text-red-600">{error}</p>}
      <button
        className="rounded-md bg-black px-3 py-2 text-white disabled:opacity-50"
        disabled={busy}
      >
        {busy ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}

export default function Chat() {
  const [session, setSession] = useState<Session | null>(null);

  // sessionStorage / randomUUID only exist in the browser; load after mount.
  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setSession(loadSession()), []);

  if (!session) return <main className="p-4">Loading…</main>;

  const update = (s: Session) => {
    saveSession(s);
    setSession(s);
  };

  async function signOut() {
    await fetch("/api/auth/logout", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ threadId: session!.threadId }),
    }).catch(() => {});
    update({ threadId: crypto.randomUUID(), name: null }); // fresh thread = fresh chat
  }

  return (
    <main className="mx-auto flex h-screen max-w-3xl flex-col p-4">
      <header className="mb-3 flex items-center justify-between">
        <h1 className="text-xl font-semibold">Shopping assistant</h1>
        {session.name && (
          <div className="flex items-center gap-3 text-sm">
            <span>{session.name}</span>
            <button className="rounded-md border px-2 py-1" onClick={signOut}>
              Sign out
            </button>
          </div>
        )}
      </header>
      {session.name ? (
        <div className="min-h-0 flex-1 overflow-hidden rounded-xl border">
          <CopilotKit
            runtimeUrl="/api/copilotkit"
            agent="ecommerce_agent"
            threadId={session.threadId}
          >
            <CopilotChat
              className="h-full"
              labels={{
                title: "Shopping assistant",
                initial: `Hi ${session.name}! What would you like to do today?`,
              }}
            />
          </CopilotKit>
        </div>
      ) : (
        <SignIn
          threadId={session.threadId}
          onSignedIn={(name) => update({ ...session, name })}
        />
      )}
    </main>
  );
}
