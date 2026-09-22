import { useEffect, useState } from "react";
import { getJSON } from "../api/client";

export default function Policy() {
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    getJSON("/policy/search").then(setData).catch((e) => setData({ error: String(e) }));
  }, []);

  return (
    <div data-testid="page-policy">
      <h1>Policy</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
