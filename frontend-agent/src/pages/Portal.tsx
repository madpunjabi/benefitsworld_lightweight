import { useEffect, useState } from "react";
import { getJSON } from "../api/client";

export default function Portal() {
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    getJSON("/portal/case").then(setData).catch((e) => setData({ error: String(e) }));
  }, []);

  return (
    <div data-testid="page-portal">
      <h1>Portal</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
