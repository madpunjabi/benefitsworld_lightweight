import { useEffect, useState } from "react";
import { getJSON } from "../api/client";

export default function Calendar() {
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    getJSON("/calendar/events").then(setData).catch((e) => setData({ error: String(e) }));
  }, []);

  return (
    <div data-testid="page-calendar">
      <h1>Calendar</h1>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
