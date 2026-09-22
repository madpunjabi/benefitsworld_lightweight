import { useCallback, useEffect, useState } from "react";
import { labGet, labPost } from "../api/labClient";

interface WorldState {
  scenario_id: string;
  scenario_version: string;
  current_sim_day: number;
  case_status: string;
  case_id: string;
  open_requirements: string[];
}

export default function LabConsole() {
  const [state, setState] = useState<WorldState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [advanceTo, setAdvanceTo] = useState("18");

  const refresh = useCallback(() => {
    labGet<WorldState>("/lab/world_state")
      .then((s) => {
        setState(s);
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
        <dl>
          <dt>Scenario ID</dt>
          <dd data-testid="lab-scenario-id">{state.scenario_id}</dd>
          <dt>Current simulated day</dt>
          <dd data-testid="lab-sim-day">{state.current_sim_day}</dd>
          <dt>Case status (backend truth)</dt>
          <dd data-testid="lab-case-status">{state.case_status}</dd>
        </dl>
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
