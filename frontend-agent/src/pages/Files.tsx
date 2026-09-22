import { useEffect, useState } from "react";
import { getJSON } from "../api/client";
import type { DocumentOut } from "../api/types";

export default function Files() {
  const [files, setFiles] = useState<DocumentOut[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    getJSON<DocumentOut[]>("/files").then((docs) => {
      setFiles(docs);
      if (docs.length > 0) setSelectedId(docs[0].id);
    });
  }, []);

  const selected = files.find((f) => f.id === selectedId) ?? null;

  return (
    <div data-testid="page-files">
      <h2>My Files</h2>
      <div className="two-column">
        <div className="list-pane">
          {files.map((f) => (
            <div
              key={f.id}
              className={`file-list-item${f.id === selectedId ? " selected" : ""}`}
              data-testid={`file-item-${f.id}`}
              onClick={() => setSelectedId(f.id)}
            >
              <div>{f.filename}</div>
              <div className="muted">
                {f.type} · {f.date}
              </div>
            </div>
          ))}
        </div>
        <div className="detail-pane" data-testid="file-preview">
          {selected ? (
            <>
              <h3>{selected.filename}</h3>
              <p className="muted">
                Type: {selected.type} · Date: {selected.date}
              </p>
              <p data-testid="file-preview-text">{selected.visible_text}</p>
            </>
          ) : (
            <p className="muted">Select a file to preview it.</p>
          )}
        </div>
      </div>
    </div>
  );
}
