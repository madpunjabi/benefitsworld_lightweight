# BenefitsWorld

A lightweight benchmark environment for testing whether an AI agent can hold
**longitudinal responsibility** for a household's CalFresh (food assistance) case
— navigating a realistic multi-page county portal, reading notices, submitting the
right documents, and keeping the case in good standing as facts, requirements, and
simulated time change.

It has two surfaces:

- **Agent view** — the county Case Portal an agent (or a person) interacts with.
- **Lab Console** — a researcher view showing the hidden ground truth, plus controls
  to reset the world, switch scenarios, and advance simulated time.

---

## 1. Try it now — hosted, no install

| Surface | URL |
| --- | --- |
| **Agent view** (drive the case) | https://benefitsworld-agent.vercel.app |
| **Lab Console** (researcher controls) | https://benefitsworld-lab.vercel.app |

Lab Console password: **`benefitsforall`**

**A 2-minute walkthrough:**
1. Open the **Lab Console**, log in, make sure the scenario is **BW-001**, and click
   **Reset environment**. The **World truth** panel now shows a clean Day-0 case
   (status `PENDING`, one open requirement: `earned_income_verification`).
2. Click **Open Agent View** (or open the agent URL). You are now looking at what the
   agent sees — with none of the ground truth.
3. Resolve the case by hand: check **My Files**, then on the Case Portal pick the
   correct document for **Earned Income Verification** and upload it. Watch the
   **World truth** panel in the Lab Console update as state changes.

> The hosted backend is a **single shared world** (one database). If several people
> use it at once they will affect each other's state — just hit **Reset** to start clean.

---

## 2. Run it locally

**Prerequisites:** Python **3.11 or 3.12**, Node **18+**, and `git`.

```bash
git clone https://github.com/madpunjabi/benefitsworld_lightweight.git
cd benefitsworld_lightweight
./init.sh
```

`init.sh` creates the Python virtualenv, installs backend + both frontend
dependencies on first run, and starts all three services. Then open:

| Surface | URL |
| --- | --- |
| Agent view | http://localhost:5173 |
| Lab Console | http://localhost:5174 |
| Backend API | http://localhost:8000 |

Local Lab Console password: **`dev-lab-password-benefitsworld-local-only`**

No environment variables are required for local use — the frontends default to the
local backend. Press **Ctrl-C** to stop everything.

> If dependency install fails while building `pydantic-core`, you are on Python 3.14+;
> use Python 3.11 or 3.12 instead.

---

## 3. The AI agent (the capability being demonstrated)

The point of the environment is to be driven by an **AI agent** operating under
realistic constraints: browser-only access, no visibility into ground truth, and the
requirement to verify its own actions and ask the household when a fact is genuinely
missing.

**To see a run without any setup:** the Lab Console shows a **"BW-001 — Pilot Run 1"**
card (a recorded result: model, success/failure, browser-action count, and cost), and
the `runs/` directory holds saved run artifacts. This is the recommended way for a
reviewer to see the agent's behavior.

**Running a live agent yourself is optional and heavier** — it requires an agent
runner (a separate Claude process driving a browser via automation) and your own
Anthropic API key, and each full run costs real inference budget. It is not needed to
evaluate or interact with the prototype.

---

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
