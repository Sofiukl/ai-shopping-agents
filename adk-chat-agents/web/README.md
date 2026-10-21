# web

Next.js + [CopilotKit](https://docs.copilotkit.ai) chat UI for the shopping agent.

- `components/Chat.tsx`: sign-in form, then `CopilotChat`. The thread ID and user name are kept in
  `sessionStorage`, so a refresh keeps you signed in.
- `app/api/copilotkit/route.ts`: CopilotKit runtime, forwarding to the agent's AG-UI endpoint.
- `app/api/auth/*`: sign-in/out proxies to the agent server, so credentials never enter the chat.

```sh
npm install
npm run dev          # http://localhost:3000; needs `uv run shop-agent-server` on :8001
```

`AGENT_URL` (default `http://127.0.0.1:8001`) points the web app at a different agent server.
