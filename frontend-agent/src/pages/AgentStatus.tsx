import { useEffect, useState } from "react";
import { getJSON } from "../api/client";

export default function AgentStatus() {
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    getJSON("/agent/status").then(setData).catch((e) => setData({ error: String(e) }));
  }, []);

  return (
    <div data-testid="page-agent">
      <h1>Agent Status</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
