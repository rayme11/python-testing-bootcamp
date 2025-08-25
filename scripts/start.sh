#!/usr/bin/env bash
# ==============================================================================
# scripts/start.sh
# Idempotent bootstrapper:
# - Ensures day-by-day folder structure (days/day1..dayN) with placeholder README.md (no overwrite)
# - Installs Python deps (if requirements.txt present)
# - Starts MongoDB, seeds DB (if scripts/seed_data.py present)
# - Starts FastAPI (Uvicorn) with GraphQL (expects src.main:app)
# - Prints helpful URLs (Codespaces-aware)
# ==============================================================================

set -Eeuo pipefail

# ----------------------------
# Config (override via env var)
# ----------------------------
HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"
APP_MODULE="${APP_MODULE:-src.main:app}"
DB_PATH="${DB_PATH:-/data/db}"
MONGO_HOST="${MONGO_HOST:-127.0.0.1}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_URI="${MONGO_URI:-mongodb://${MONGO_HOST}:${MONGO_PORT}}"
DAYS_ROOT="${DAYS_ROOT:-days}"
TOTAL_DAYS="${TOTAL_DAYS:-30}"
RUN_TESTS="${RUN_TESTS:-0}"   # set 1 to auto-run tests after boot
SEED_COUNT="${SEED_COUNT:-10}" # optional (used by your seed script if it reads env)

# --------------------------------
# Pretty printing helpers (colors)
# --------------------------------
BOLD="\033[1m"; DIM="\033[2m"; RED="\033[31m"; GREEN="\033[32m"; YELLOW="\033[33m"; BLUE="\033[34m"; NC="\033[0m"
log()   { echo -e "${BOLD}${BLUE}▶${NC} $*"; }
ok()    { echo -e "${GREEN}✓${NC} $*"; }
warn()  { echo -e "${YELLOW}!${NC} $*"; }
fail()  { echo -e "${RED}✗${NC} $*"; }

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ----------------------------
# Utilities
# ----------------------------
ensure_dir() {
  mkdir -p "$1"
  ok "Ensured dir: $1"
}

create_placeholder_readme() {
  local path="$1"
  local title="$2"
  if [[ ! -f "$path" ]]; then
    {
      echo "# ${title}"
      echo
      echo "> Placeholder: this day's detailed README will be added later."
      echo
      echo "Run:"
      echo '```bash'
      echo './scripts/start.sh'
      echo '```'
    } > "$path"
    ok "Created README: $path"
  else
    log "Exists: $path"
  fi
}

kill_if_running() {
  local pattern="$1"
  if pgrep -f "$pattern" >/dev/null 2>&1; then
    warn "Killing existing process matching: $pattern"
    pkill -f "$pattern" || true
    sleep 1
  fi
}

# ==============================================================================
# Step 1: Day-by-day folder structure (non-destructive)
# ==============================================================================
log "Ensuring day-by-day folder structure under ./${DAYS_ROOT}…"
ensure_dir "${ROOT_DIR}/${DAYS_ROOT}"

for d in $(seq 1 "${TOTAL_DAYS}"); do
  DAY_DIR="${ROOT_DIR}/${DAYS_ROOT}/day${d}"
  ensure_dir "$DAY_DIR"
  create_placeholder_readme "${DAY_DIR}/README.md" "Day ${d}"
done

# ==============================================================================
# Step 2: Install Python dependencies (if requirements.txt exists)
# ==============================================================================
if [[ -f "${ROOT_DIR}/requirements.txt" ]]; then
  log "Installing Python dependencies from requirements.txt…"
  python -m pip install --upgrade pip >/dev/null
  pip install -r "${ROOT_DIR}/requirements.txt"
  ok "Dependencies installed."
else
  warn "requirements.txt not found — skipping dependency installation."
fi

# ==============================================================================
# Step 3: Start MongoDB
# ==============================================================================
log "Starting MongoDB (if not already running)…"
ensure_dir "${ROOT_DIR}/data"
ensure_dir "${DB_PATH}"

if pgrep -x mongod >/dev/null 2>&1; then
  ok "mongod already running."
else
  if ! command -v mongod >/dev/null 2>&1; then
    fail "mongod not found. Please install MongoDB in your environment."
    echo "Debian/Ubuntu example:"
    echo "  sudo apt-get update && sudo apt-get install -y mongodb"
    exit 1
  fi
  mongod --dbpath "${DB_PATH}" --bind_ip "${MONGO_HOST}" --port "${MONGO_PORT}" \
    > "${ROOT_DIR}/data/mongod.log" 2>&1 &
  ok "mongod launched. Logs: data/mongod.log"
fi

# small wait for mongod to accept connections
sleep 2

# ==============================================================================
# Step 4: Seed database (optional — only if your seed script exists)
# ==============================================================================
if [[ -f "${ROOT_DIR}/scripts/seed_data.py" ]]; then
  log "Seeding database via scripts/seed_data.py…"
  ( cd "${ROOT_DIR}" && MONGO_URI="${MONGO_URI}" SEED_COUNT="${SEED_COUNT}" python scripts/seed_data.py ) \
    && ok "Database seeded." \
    || warn "Seeding script failed (continuing)."
else
  log "No scripts/seed_data.py found — skipping seeding."
fi

# ==============================================================================
# Step 5: Start Uvicorn (FastAPI + GraphQL)
# ==============================================================================
log "Starting FastAPI (Uvicorn) @ ${HOST}:${PORT}…"
# If an old instance of the same app is running, stop it first
kill_if_running "uvicorn .*${APP_MODULE}"

# Ensure src/main.py exists (won't create it here to avoid overwriting your codebase)
if [[ ! -f "${ROOT_DIR}/src/main.py" ]]; then
  fail "src/main.py not found. Please add your FastAPI app (app=FastAPI) at ${APP_MODULE}"
  exit 1
fi

cd "${ROOT_DIR}"
uvicorn "${APP_MODULE}" --reload --host "${HOST}" --port "${PORT}" \
  > "${ROOT_DIR}/data/uvicorn.log" 2>&1 &
ok "Uvicorn launched. Logs: data/uvicorn.log"

# ==============================================================================
# Step 6: Print Helpful URLs (Codespaces-aware)
# ==============================================================================
echo
if [[ -n "${CODESPACES:-}" && -n "${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-}" ]]; then
  # Codespaces URL pattern
  FORWARDED_URL="https://${CODESPACE_NAME}-${PORT}.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
  ok "Access URLs (Codespaces)"
  echo "   REST:     ${FORWARDED_URL}/"
  echo "   GraphQL:  ${FORWARDED_URL}/graphql"
else
  ok "Access URLs (Local/Container)"
  echo "   REST:     http://127.0.0.1:${PORT}/"
  echo "   GraphQL:  http://127.0.0.1:${PORT}/graphql"
fi
echo

# ==============================================================================
# Step 7: Optional — run tests
# ==============================================================================
if [[ "${RUN_TESTS}" == "1" ]]; then
  log "Running tests (set RUN_TESTS=0 to skip)…"
  if command -v pytest >/dev/null 2>&1; then
    pytest --maxfail=1 --disable-warnings -q || warn "Some tests failed."
  else
    warn "pytest not installed (ensure requirements.txt includes pytest)."
  fi
fi

ok "Environment ready. This script is safe to re-run — it won’t overwrite existing files."
