import { useCallback, useEffect, useState } from "react";
import { getJSON, postJSON } from "../api/client";
import type { CaseOut, DocumentOut, InterviewSlotOut, NoticeOut } from "../api/types";

function readableRequirement(requirement: string): string {
  return requirement
    .split("_")
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
}

export default function Portal() {
  const [caseData, setCaseData] = useState<CaseOut | null>(null);
  const [notices, setNotices] = useState<NoticeOut[]>([]);
  const [files, setFiles] = useState<DocumentOut[]>([]);
  const [slots, setSlots] = useState<InterviewSlotOut[]>([]);
  const [selection, setSelection] = useState<Record<string, string>>({});
  const [selectedSlot, setSelectedSlot] = useState<string>("");
  const [status, setStatus] = useState<string | null>(null);

  const refresh = useCallback(() => {
    Promise.all([
      getJSON<CaseOut>("/portal/case"),
      getJSON<NoticeOut[]>("/portal/notices"),
      getJSON<DocumentOut[]>("/files"),
      getJSON<InterviewSlotOut[]>("/portal/interview/slots"),
    ]).then(([c, n, f, s]) => {
      setCaseData(c);
      setNotices(n);
      setFiles(f);
      setSlots(s);
    });
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (!caseData) {
    return (
      <div data-testid="page-portal">
        <p>Loading case…</p>
      </div>
    );
  }

  const filenameFor = (documentId: string) =>
    files.find((f) => f.id === documentId)?.filename ?? documentId;

  const onUpload = async (requirement: string) => {
    const documentId = selection[requirement];
    if (!documentId) {
      setStatus("Select a document before uploading.");
      return;
    }
    setStatus(null);
    await postJSON("/portal/uploads", { document_id: documentId, requirement });
    setStatus(`Uploaded "${filenameFor(documentId)}" for ${readableRequirement(requirement)}.`);
    refresh();
  };

  const onScheduleInterview = async () => {
    if (!selectedSlot) {
      setStatus("Select an appointment before confirming.");
      return;
    }
    setStatus(null);
    await postJSON("/portal/interview/schedule", { slot_id: selectedSlot });
    setStatus("Interview appointment confirmed.");
    refresh();
  };

  return (
    <div data-testid="page-portal">
      <h2>Case Portal</h2>

      <section className="card" data-testid="case-summary">
        <table className="data-table">
          <tbody>
            <tr>
              <th>Case number</th>
              <td data-testid="case-id">{caseData.case_id}</td>
            </tr>
            <tr>
              <th>Status</th>
              <td>
                <span className="status-badge" data-testid="case-status">
                  {caseData.status}
                </span>
              </td>
            </tr>
            <tr>
              <th>Employer on file</th>
              <td data-testid="reported-employer">{caseData.reported_employer ?? "—"}</td>
            </tr>
            {caseData.interview && (
              <tr>
                <th>Interview</th>
                <td data-testid="interview-status">
                  Day {caseData.interview.day}, {caseData.interview.start_time}–
                  {caseData.interview.end_time} —{" "}
                  <span className="status-badge">{caseData.interview.status.toUpperCase()}</span>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section data-testid="notices">
        <h3>Notices</h3>
        {notices.length === 0 && <p className="muted">No notices at this time.</p>}
        {notices.map((notice) => (
          <div className="notice" key={notice.id}>
            {notice.text}
          </div>
        ))}
      </section>

      <section data-testid="open-requirements">
        <h3>Open Requirements</h3>
        {caseData.open_requirements.length === 0 && <p className="muted">No open requirements.</p>}
        {caseData.open_requirements.map((requirement) =>
          requirement === "interview" ? (
            <div className="card" key={requirement} data-testid="requirement-interview">
              <strong>Interview</strong>
              <p className="muted">Choose an available appointment to schedule your interview.</p>
              <select
                data-testid="interview-slot-select"
                value={selectedSlot}
                onChange={(e) => setSelectedSlot(e.target.value)}
              >
                <option value="">Select an appointment…</option>
                {slots.map((s) => (
                  <option key={s.id} value={s.id}>
                    Day {s.day}, {s.start_time}–{s.end_time}
                  </option>
                ))}
              </select>{" "}
              <button data-testid="interview-confirm-button" onClick={onScheduleInterview}>
                Confirm Appointment
              </button>
            </div>
          ) : (
            <div className="card" key={requirement} data-testid={`requirement-${requirement}`}>
              <strong>{readableRequirement(requirement)}</strong>
              <p className="muted">
                Submit a document from your files that supports this requirement.
              </p>
              <select
                data-testid={`requirement-select-${requirement}`}
                value={selection[requirement] ?? ""}
                onChange={(e) => setSelection({ ...selection, [requirement]: e.target.value })}
              >
                <option value="">Select a document…</option>
                {files.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.filename} ({f.date})
                  </option>
                ))}
              </select>{" "}
              <button
                data-testid={`requirement-upload-${requirement}`}
                onClick={() => onUpload(requirement)}
              >
                Upload
              </button>
            </div>
          ),
        )}
      </section>

      {status && (
        <p className="notice" data-testid="upload-status">
          {status}
        </p>
      )}

      <section className="card" data-testid="received-documents">
        <h3>Received Documents</h3>
        {caseData.received_document_ids.length === 0 && (
          <p className="muted">No documents received yet.</p>
        )}
        <ul>
          {caseData.received_document_ids.map((documentId) => (
            <li key={documentId} data-testid={`received-doc-${documentId}`}>
              <span className="received-tag">✓ Received</span> {filenameFor(documentId)}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
