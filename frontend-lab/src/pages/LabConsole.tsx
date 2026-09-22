import { useCallback, useEffect, useState } from "react";
import { labGet, labPost } from "../api/labClient";

interface LabUpload {
  id: number;
  document_id: string;
  requirement: string;
  attempted_at_day: number;
  ui_reported_success: boolean;
  actually_persisted: boolean;
  scripted_failure_id: string | null;
}

interface LabSilentFailure {
  id: string;
  document_id: string;
  requirement: string;
  consumed: boolean;
}

interface LabIncomeTruth {
  document_id: string;
  filename: string;
  visible_text: string;
}

interface WorldState {
  scenario_id: string;
  scenario_version: string;
  current_sim_day: number;
  case_status: string;
  case_id: string;
  open_requirements: string[];
  interview: Record<string, unknown> | null;
  applied_event_ids: string[];
  pending_event_ids: string[];
  uploads: LabUpload[];
  silent_failures: LabSilentFailure[];
  income_truth_document: LabIncomeTruth | null;
}

interface EvaluateResult {
  binary_success: boolean;
  checkpoints: Record<string, boolean>;
}

export default function LabConsole() {
  const [state, setState] = useState<WorldState | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluateResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [advanceTo, setAdvanceTo] = useState("18");

  const refresh = useCallback(() => {
    Promise.all([labGet<WorldState>("/lab/world_state"), labGet<EvaluateResult>("/lab/evaluate")])
      .then(([s, e]) => {
        setState(s);
        setEvaluation(e);
        setError(null);
      })
      .catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const onReset = async () => {
    await labPost("/lab/reset");
    refresh();
  };

  const onAdvance = async () => {
    await labPost("/lab/clock/advance", { to_day: Number(advanceTo) });
    refresh();
  };

  return (
    <div data-testid="page-lab-console">
      <h1>BenefitsWorld Lab Console</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {state && (
        <>
          <dl>
            <dt>Scenario ID</dt>
            <dd data-testid="lab-scenario-id">{state.scenario_id}</dd>
            <dt>Current simulated day</dt>
            <dd data-testid="lab-sim-day">{state.current_sim_day}</dd>
            <dt>Case status (backend truth)</dt>
            <dd data-testid="lab-case-status">{state.case_status}</dd>
            <dt>Open requirements</dt>
            <dd data-testid="lab-open-requirements">
              {state.open_requirements.length ? state.open_requirements.join(", ") : "(none)"}
            </dd>
            <dt>Interview</dt>
            <dd data-testid="lab-interview">
              {state.interview ? JSON.stringify(state.interview) : "(not scheduled)"}
            </dd>
            <dt>Applied event IDs</dt>
            <dd data-testid="lab-applied-events">
              {state.applied_event_ids.length ? state.applied_event_ids.join(", ") : "(none)"}
            </dd>
            <dt>Pending event IDs</dt>
            <dd data-testid="lab-pending-events">{state.pending_event_ids.join(", ")}</dd>
            <dt>Current employer/income truth</dt>
            <dd data-testid="lab-income-truth">
              {state.income_truth_document
                ? `${state.income_truth_document.document_id}: ${state.income_truth_document.visible_text}`
                : "(unknown)"}
            </dd>
          </dl>

          <h2>Scripted failures</h2>
          <table data-testid="lab-silent-failures-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Document</th>
                <th>Requirement</th>
                <th>Fired</th>
              </tr>
            </thead>
            <tbody>
              {state.silent_failures.map((f) => (
                <tr key={f.id}>
                  <td>{f.id}</td>
                  <td>{f.document_id}</td>
                  <td>{f.requirement}</td>
                  <td data-testid={`lab-failure-fired-${f.id}`}>{String(f.consumed)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h2>Canonical uploads</h2>
          {state.uploads.length === 0 ? (
            <p>(none)</p>
          ) : (
            <table data-testid="lab-uploads-table">
              <thead>
                <tr>
                  <th>Document</th>
                  <th>Requirement</th>
                  <th>Day</th>
                  <th>UI reported success</th>
                  <th>Actually persisted</th>
                  <th>Scripted failure</th>
                </tr>
              </thead>
              <tbody>
                {state.uploads.map((u) => (
                  <tr key={u.id}>
                    <td>{u.document_id}</td>
                    <td>{u.requirement}</td>
                    <td>{u.attempted_at_day}</td>
                    <td>{String(u.ui_reported_success)}</td>
                    <td>{String(u.actually_persisted)}</td>
                    <td>{u.scripted_failure_id ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}

          {evaluation && (
            <>
              <h2>Evaluator (research-only)</h2>
              <dl>
                <dt>Binary success</dt>
                <dd data-testid="lab-binary-success">{String(evaluation.binary_success)}</dd>
              </dl>
              <table data-testid="lab-checkpoints-table">
                <tbody>
                  {Object.entries(evaluation.checkpoints).map(([name, value]) => (
                    <tr key={name}>
                      <td>{name}</td>
                      <td data-testid={`lab-checkpoint-${name}`}>{String(value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </>
          )}
        </>
      )}
      <div>
        <button data-testid="lab-reset-button" onClick={onReset}>
          Reset environment
        </button>
      </div>
      <div>
        <input
          data-testid="lab-advance-input"
          value={advanceTo}
          onChange={(e) => setAdvanceTo(e.target.value)}
        />
        <button data-testid="lab-advance-button" onClick={onAdvance}>
          Advance simulated time
        </button>
      </div>
    </div>
  );
}
