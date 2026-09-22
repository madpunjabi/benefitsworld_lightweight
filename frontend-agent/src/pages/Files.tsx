import { useEffect, useState } from "react";
import { getJSON } from "../api/client";

export default function Files() {
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    getJSON("/files").then(setData).catch((e) => setData({ error: String(e) }));
  }, []);

  return (
    <div data-testid="page-files">
      <h1>Files</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
