# BenefitsWorld

A benchmark that tests whether an AI agent can hold **durable responsibility** for a
household's CalFresh (food assistance) case — operating a realistic multi-page county
portal, reading notices, submitting the right documents, catching silent failures, and
keeping the case in good standing as facts, requirements, and simulated time change.

## ⚡ Try it in 60 seconds — no install, nothing to set up

Open these two links in your browser:

1. **Lab Console (researcher view)** → **https://benefitsworld-lab.vercel.app**
   - Password: **`benefitsforall`**
   - Make sure the scenario says **BW-001**, then click **Reset environment**.
2. **Agent view (what the AI operates)** → **https://benefitsworld-agent.vercel.app**
   - This is the county Case Portal, with none of the hidden answers.

**Then try the task yourself (you play the agent):**
1. In the Agent view, open **My Files** to see the household's documents.
2. On the **Case Portal**, under *Earned Income Verification*, pick the current paystub
   and click **Upload**.
3. Back in the **Lab Console**, watch the **World truth** panel — the requirement clears.
4. In the Lab Console, set **Advance simulated time** to `3`, then `18`, and watch new
   requirements, an interview, a silent upload failure, and a mid-case employment change
   appear over time. That longitudinal pressure is the whole point.

> The hosted backend is one shared demo world. If it looks mid-progress, just click
> **Reset environment** in the Lab Console to start clean.

That's everything a reviewer needs. The sections below are for running it yourself or
reading the code.

---

## What the two surfaces are

- **Agent view** — the county Case Portal an AI agent (or a person) operates.
- **Lab Console** — the researcher view: the ground truth hidden from the agent, plus
  controls to reset the world, switch scenarios, and advance simulated time.

## Run it locally

**Prerequisites:** Python **3.11 or 3.12**, Node **18+**, and `git`.

```bash
git clone https://github.com/madpunjabi/benefitsworld_lightweight.git
cd benefitsworld_lightweight
./init.sh
```

`init.sh` creates the Python virtualenv, installs backend + both frontend dependencies
on first run, and starts all three services. Then open:

| Surface | URL |
| --- | --- |
| Agent view | http://localhost:5173 |
| Lab Console | http://localhost:5174 |
| Backend API | http://localhost:8000 |

Local Lab Console password: **`dev-lab-password-benefitsworld-local-only`**

No environment variables are needed — the frontends default to the local backend. Press
**Ctrl-C** to stop everything.

> If dependency install fails while building `pydantic-core`, you are on Python 3.14+;
> use Python 3.11 or 3.12 instead.

## The AI agent (the capability being demonstrated)

The environment is built to be driven by an **AI agent** under realistic constraints:
browser-only access, no visibility into ground truth, and the need to verify its own
actions and recover from failures over simulated days.

- **See a run with zero setup:** the Lab Console shows a recorded pilot-run result
  (model, success/failure, action count, cost), and the `runs/` directory holds saved
  run artifacts.
- **Run a live agent yourself (optional, heavier):** requires a separate agent runner
  driving a browser via automation and your own Anthropic API key. Not needed to
  evaluate or interact with the prototype.

## Repo layout

| Path | What it is |
| --- | --- |
| `backend/` | FastAPI app: world state, scenarios, reset, simulated time, evaluator |
| `frontend-agent/` | The agent-facing Case Portal (React + Vite) |
| `frontend-lab/` | The researcher Lab Console (React + Vite) |
| `data/` | Scenario seeds and the policy library |
| `runs/` | Saved benchmark run artifacts |
| `*_SPEC.md`, `prompts/`, `progress.md` | Design specs and build history |
| `init.sh` | One-command local startup |
