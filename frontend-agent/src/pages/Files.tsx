import { useEffect, useState } from "react";
import { getJSON } from "../api/client";
import type { DocumentOut } from "../api/types";

export default function Files() {
  const [files, setFiles] = useState<DocumentOut[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [selectedDoc, setSelectedDoc] = useState<DocumentOut | null>(null);

  useEffect(() => {
    getJSON<DocumentOut[]>("/files").then((docs) => {
      setFiles(docs);
      if (docs.length > 0) setSelectedId(docs[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setSelectedDoc(null);
      return;
    }
    // A real, logged "open this document" request — not just a client-side
    // switch over data already fetched with the list — so inspecting a
    // specific file is a genuine, structurally-visible action.
    getJSON<DocumentOut>(`/files/${selectedId}`).then(setSelectedDoc);
  }, [selectedId]);

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
          {selectedDoc ? (
            <>
              <h3>{selectedDoc.filename}</h3>
              <p className="muted">
                Type: {selectedDoc.type} · Date: {selectedDoc.date}
              </p>
              <p data-testid="file-preview-text">{selectedDoc.visible_text}</p>
            </>
          ) : (
            <p className="muted">Select a file to preview it.</p>
          )}
        </div>
      </div>
    </div>
  );
}
