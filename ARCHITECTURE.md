# Architecture

## Stack
- React + Vite frontend
- FastAPI backend
- SQLite persistence
- Playwright browser automation
- Separate Python benchmark-agent runner

## Agent-visible apps
- `/portal` — case status, requirements, uploads, notices, interview scheduling
- `/inbox` — synthetic agency messages
- `/files` — household documents and distractors
- `/calendar` — conflicts + interview
- `/policy` — frozen policy library
- `/agent` — household-facing status/questions

## Research-only app
- `/lab` — actual world state, agent belief, simulated day, events, evaluator predicates, failure labels, run comparison

The benchmark agent must never access `/lab` or evaluator endpoints.

## Four distinct states
1. World state — simulator truth
2. Visible state — what the apps expose
3. Agent belief — what the model thinks
4. Evaluator state — scoring logic

Never collapse these.

## Backend modules
- scenario_loader.py
- world_state.py
- event_engine.py
- clock.py
- policy_store.py
- action_log.py
- evaluator.py
- reset.py
- agent_runner.py

## Core principle
A click is not an outcome. Consequential actions require independent verification of external state.
