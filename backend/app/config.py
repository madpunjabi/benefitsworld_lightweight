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

# Deployment-only: a single flag distinguishing a hosted deployment from
# local development. Everything defaults to preserving today's local
# behavior (always reset on boot; cookies work over plain localhost
# HTTP) unless ENVIRONMENT=production is set explicitly — see main.py's
# lifespan and security.py's session cookie attributes.
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# RESET_ON_BOOT preserves the exact original Milestone-1 behavior (always
# reset to a deterministic Day-0 state on process start) for local dev
# and tests. In production it defaults to False, so a Railway process
# restart does not silently wipe a live demo — see main.py's lifespan,
# which then only initializes the database if it isn't already
# initialized, and otherwise preserves it untouched. Reset itself remains
# available at any time via the existing explicit POST /lab/reset action.
RESET_ON_BOOT = os.environ.get("RESET_ON_BOOT", "false" if IS_PRODUCTION else "true").lower() == "true"

DATABASE_PATH = os.environ.get("DATABASE_PATH", str(REPO_ROOT / "backend" / "benefitsworld.db"))

# Demo-only Lab Console login (see security.py). Never sent to, or
# embedded in, any frontend bundle.
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-session-secret-benefitsworld-local-only")
LAB_CONSOLE_PASSWORD = os.environ.get("LAB_CONSOLE_PASSWORD", "dev-lab-password-benefitsworld-local-only")

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
