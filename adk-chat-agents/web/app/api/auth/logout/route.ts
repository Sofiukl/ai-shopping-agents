import { AGENT_URL } from "@/lib/agent";

export async function POST(req: Request) {
  const { threadId } = await req.json();
  const resp = await fetch(`${AGENT_URL}/auth/logout`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ thread_id: threadId }),
  });
  return Response.json({ status: resp.ok ? "ok" : "error" }, { status: resp.status });
}
