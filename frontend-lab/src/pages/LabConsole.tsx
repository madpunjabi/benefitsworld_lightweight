import { useCallback, useEffect, useState } from "react";
import { AGENT_URL, labGet, labPost } from "../api/labClient";

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
  recertification: Record<string, unknown> | null;
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

export default function LabConsole({ onLogout }: { onLogout: () => void }) {
  const [state, setState] = useState<WorldState | null>(null);
  const [evaluation, setEvaluation] = useState<EvaluateResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [advanceTo, setAdvanceTo] = useState("18");
  const [scenario, setScenario] = useState("BW-001");

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
    await labPost("/lab/reset", { scenario_id: scenario });
    refresh();
  };

  const onAdvance = async () => {
    await labPost("/lab/clock/advance", { to_day: Number(advanceTo) });
    refresh();
  };

  const onLogoutClick = async () => {
    await labPost("/lab/logout");
    onLogout();
  };

  return (
    <div data-testid="page-lab-console">
      <header>
        <h1>BenefitsWorld</h1>
        <h2>Lab Console</h2>
        <p className="muted">
          A benchmark environment for testing whether an AI agent can maintain responsibility for a
          household's CalFresh case as facts, software state, requirements, and simulated time change.
        </p>
        <p data-testid="lab-ground-truth-badge">
          <strong>Researcher view</strong> — shows ground truth hidden from the benchmark agent
        </p>
        <p>
          <a href={AGENT_URL} target="_blank" rel="noreferrer" data-testid="lab-open-agent-view">
            Open Agent View
          </a>{" "}
          <button data-testid="lab-logout-button" onClick={onLogoutClick}>
            Log out
          </button>
        </p>
      </header>

      <section data-testid="lab-run1-result-card" className="card">
        <h3>BW-001 — Pilot Run 1</h3>
        <p className="muted">Recorded experiment result — not live state.</p>
        <dl>
          <dt>Model</dt>
          <dd>Fable 5.1</dd>
          <dt>Result</dt>
          <dd>SUCCESS</dd>
          <dt>Browser actions</dt>
          <dd>196</dd>
          <dt>Inference cost</dt>
          <dd>~$16.78</dd>
        </dl>
      </section>

      <section data-testid="lab-bw002-note" className="card">
        <h3>BW-002</h3>
        <p className="muted">Research iteration — evaluator ambiguity identified.</p>
      </section>

      {error && <p style={{ color: "red" }}>{error}</p>}
      {state && (
        <>
          <div>
            <label>
              Scenario{" "}
              <select
                data-testid="lab-scenario-select"
                value={scenario}
                onChange={(e) => setScenario(e.target.value)}
              >
                <option value="BW-001">BW-001</option>
                <option value="BW-002">BW-002</option>
              </select>
            </label>{" "}
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

          <h2>World truth</h2>
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
            <dt>Recertification</dt>
            <dd data-testid="lab-recertification">
              {state.recertification ? JSON.stringify(state.recertification) : "(not applicable)"}
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
    </div>
  );
}
