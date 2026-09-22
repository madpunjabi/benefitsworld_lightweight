import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPO_ROOT / ".env")

LAB_TOKEN = os.environ.get("LAB_TOKEN", "dev-lab-token-benefitsworld-local-only")
SCENARIO_ID = os.environ.get("SCENARIO_ID", "BW-001")
SCENARIO_VERSION = os.environ.get("SCENARIO_VERSION", "0.1")
AGENT_ORIGIN = os.environ.get("AGENT_ORIGIN", "http://localhost:5173")
LAB_ORIGIN = os.environ.get("LAB_ORIGIN", "http://localhost:5174")

DB_PATH = os.environ.get("DB_PATH", str(REPO_ROOT / "backend" / "benefitsworld.db"))
SCENARIO_SEED_PATH = REPO_ROOT / "data" / "BW001_starter.json"
