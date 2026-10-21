import { Suspense } from "react";
import { connection } from "next/server";
import Chat from "@/components/Chat";

// CopilotKit creates random IDs while rendering, which cacheComponents won't prerender:
// opt this route into request-time rendering.
async function DynamicChat() {
  await connection();
  return <Chat />;
}

export default function Page() {
  return (
    <Suspense fallback={<main className="p-4">Loading…</main>}>
      <DynamicChat />
    </Suspense>
  );
}
