import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { HttpAgent } from "@ag-ui/client";
import { NextRequest } from "next/server";

// The shop agent (ADK + AG-UI) runs separately: `uv run shop-agent-server` (default port 8001).
const AGENT_URL = process.env.AGENT_URL ?? "http://127.0.0.1:8001/";

const runtime = new CopilotRuntime({
  agents: {
    ecommerce_agent: new HttpAgent({ url: AGENT_URL }),
  },
});

export const POST = async (req: NextRequest) => {
  const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
    runtime,
    serviceAdapter: new ExperimentalEmptyAdapter(),
    endpoint: "/api/copilotkit",
  });
  return handleRequest(req);
};
