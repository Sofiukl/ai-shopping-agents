import { AGENT_URL } from "@/lib/agent";

// Credentials go browser -> here -> agent server -> shop API. They never enter the chat stream.
export async function POST(req: Request) {
  const { threadId, email, password } = await req.json();
  const resp = await fetch(`${AGENT_URL}/auth/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, email, password }),
  });
  const body = await resp.json().catch(() => ({ detail: "Unexpected response" }));
  return Response.json(body, { status: resp.status });
}
