import { useEffect, useState } from "react";
import { getJSON } from "../api/client";
import type { PolicyItemOut } from "../api/types";

export default function Policy() {
  const [items, setItems] = useState<PolicyItemOut[]>([]);
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const search = (q: string) => {
    const path = q ? `/policy/search?q=${encodeURIComponent(q)}` : "/policy/search";
    getJSON<PolicyItemOut[]>(path).then((results) => {
      setItems(results);
      setSelectedId(results.length > 0 ? results[0].id : null);
    });
  };

  useEffect(() => {
    search("");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selected = items.find((i) => i.id === selectedId) ?? null;

  return (
    <div data-testid="page-policy">
      <h2>Policy Library</h2>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          search(query);
        }}
      >
        <input
          type="text"
          placeholder="Search policy…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          data-testid="policy-search-input"
        />{" "}
        <button type="submit" data-testid="policy-search-button">
          Search
        </button>
      </form>

      <div className="two-column">
        <div className="list-pane">
          {items.length === 0 && <p className="muted">No matching policy items.</p>}
          {items.map((item) => (
            <div
              key={item.id}
              className={`policy-list-item${item.id === selectedId ? " selected" : ""}`}
              data-testid={`policy-item-${item.id}`}
              onClick={() => setSelectedId(item.id)}
            >
              <div>{item.title}</div>
              <div className="muted">{item.topic.replace(/_/g, " ")}</div>
            </div>
          ))}
        </div>
        <div className="detail-pane" data-testid="policy-detail">
          {selected ? (
            <>
              <h3>{selected.title}</h3>
              <p className="muted">
                Source: {selected.source}
                {selected.source_url ? (
                  <>
                    {" "}
                    (<span data-testid="policy-source-url">{selected.source_url}</span>)
                  </>
                ) : null}
                <br />
                Jurisdiction: {selected.jurisdiction} · Effective: {selected.effective_date}
              </p>
              <p data-testid="policy-detail-text">{selected.text}</p>
            </>
          ) : (
            <p className="muted">Select a policy item to read it.</p>
          )}
        </div>
      </div>
    </div>
  );
}
