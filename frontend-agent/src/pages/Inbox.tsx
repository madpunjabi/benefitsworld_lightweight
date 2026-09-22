import { useEffect, useState } from "react";
import { getJSON } from "../api/client";

export default function Inbox() {
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    getJSON("/inbox/messages").then(setData).catch((e) => setData({ error: String(e) }));
  }, []);

  return (
    <div data-testid="page-inbox">
      <h1>Inbox</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
