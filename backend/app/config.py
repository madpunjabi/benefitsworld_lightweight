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

# One seed file per scenario. SCENARIO_SEED_PATH keeps its historical
# meaning (the seed for whichever scenario this process boots into, from
# SCENARIO_ID) so every existing BW-001 caller is unaffected; the mapping
# additionally lets reset() load a specific scenario's seed on demand
# (see scenario_loader.load_seed / reset.reset).
SCENARIO_SEED_PATHS = {
    "BW-001": REPO_ROOT / "data" / "BW001_starter.json",
    "BW-002": REPO_ROOT / "data" / "BW002_starter.json",
}
SCENARIO_SEED_PATH = SCENARIO_SEED_PATHS.get(SCENARIO_ID, SCENARIO_SEED_PATHS["BW-001"])
POLICY_LIBRARY_PATH = REPO_ROOT / "data" / "policy_library.json"
