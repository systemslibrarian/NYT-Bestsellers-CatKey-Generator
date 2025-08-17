#!/bin/bash
# This first line is called a "shebang." It tells the operating system to use the
# Bash interpreter to execute this script, making it a runnable program.

# ============================================================================
# run_nyt_script.sh
# A robust runner script for the main Python application. Its job is to set up
# the environment (API keys, settings, flags) and then execute the Python script.
# This approach keeps configuration separate from the core application logic.
# ============================================================================
#
# --- How it Works ---
# This script sets a series of environment variables based on defaults and
# any command-line options you provide. It can also load a .env file.
# Then it exports those variables so the Python script can read them and runs it.
#
# --- Command-Line Options ---
#   --debug         : Enables verbose logging (NYT_DEBUG=1).
#   --no-debug      : Disables verbose logging (NYT_DEBUG=0).
#   --lists "a,b"   : Overrides the set of bestseller lists.
#   --no-email      : Generates reports but skips sending email.
#   --quick-test    : Shortcut to process only "hardcover-fiction".
#   --env PATH      : Load variables from the specified .env file.
#
# ============================================================================

# --- SECTION 1: SCRIPT SETUP ---
# -e: exit on error
# -u: error on unset variables
# -o pipefail: fail a pipeline if any command fails
set -euo pipefail

# --- SECTION 2: INITIALIZE DEFAULTS ---
NYT_DEBUG="${NYT_DEBUG:-0}"   # default off
LISTS_OVERRIDE=""
NO_EMAIL=0
ENV_FILE=""

# --- SECTION 3: PARSE COMMAND-LINE ARGUMENTS ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug)        NYT_DEBUG=1; shift ;;
    --no-debug)     NYT_DEBUG=0; shift ;;
    --lists)        LISTS_OVERRIDE="${2:-}"; shift 2 ;;
    --no-email)     NO_EMAIL=1; shift ;;
    --quick-test)   LISTS_OVERRIDE="hardcover-fiction"; shift ;;
    --env)          ENV_FILE="${2:-}"; shift 2 ;;
    *)
      echo "Unknown option: $1" >&2; exit 2
      ;;
  esac
done

# --- SECTION 4: OPTIONAL .env LOADING ---
# If an .env is provided or present in the current directory, load it.
if [[ -n "${ENV_FILE}" ]]; then
  if [[ -f "${ENV_FILE}" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    set +a
  else
    echo "WARN: --env file not found: ${ENV_FILE}" >&2
  fi
elif [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source ./.env
  set +a
fi

# --- SECTION 5: SET UP ENV VARS (NO SECRETS HARD-CODED) ---
# Safe defaults where appropriate; secrets & keys must come from env/.env.

# SMTP defaults (can be overridden in env/.env)
export SMTP_SERVER="${SMTP_SERVER:-smtp.gmail.com}"
export SMTP_PORT="${SMTP_PORT:-587}"

# ChromeDriver default
export CHROMEDRIVER_PATH="${CHROMEDRIVER_PATH:-/usr/local/bin/chromedriver}"

# Output + logs default to project-local folders
export NYT_OUTPUT_DIR="${NYT_OUTPUT_DIR:-$PWD/reports}"
export NYT_LOG_DIR="${NYT_LOG_DIR:-$PWD/logs}"

# Bestseller lists
DEFAULT_LISTS="hardcover-fiction,hardcover-nonfiction,picture-books,childrens-middle-grade-hardcover,young-adult-hardcover"
if [[ -n "${LISTS_OVERRIDE}" ]]; then
  export NYT_LIST_NAMES="${LISTS_OVERRIDE}"
else
  export NYT_LIST_NAMES="${NYT_LIST_NAMES:-$DEFAULT_LISTS}"
fi

# Final flags
export NYT_DEBUG
export NYT_NO_EMAIL="${NO_EMAIL}"
export PYTHONUNBUFFERED=1

# --- SECTION 6: SANITY CHECKS (REQUIRED VARS) ---
missing=()
[[ -z "${SENDER_EMAIL:-}"        ]] && missing+=("SENDER_EMAIL")
[[ -z "${SENDER_PASSWORD:-}"     ]] && missing+=("SENDER_PASSWORD")
[[ -z "${RECEIVER_EMAILS:-}"     ]] && missing+=("RECEIVER_EMAILS")
[[ -z "${NYT_API_KEY:-}"         ]] && missing+=("NYT_API_KEY")
[[ -z "${CATALOG_BASE_URL:-}"    ]] && missing+=("CATALOG_BASE_URL")

if (( ${#missing[@]} > 0 )); then
  echo "FATAL: missing env vars: ${missing[*]}" >&2
  echo "Hint: copy .env.example to .env and fill in your values, or pass --env /path/to/.env" >&2
  exit 1
fi

# Ensure directories exist
mkdir -p "$NYT_OUTPUT_DIR" "$NYT_LOG_DIR"

# --- SECTION 7: STARTUP SUMMARY ---
echo "=== Startup ==="
echo "Time: $(date -Is)"
echo "Debug (NYT_DEBUG): $NYT_DEBUG"
echo "No email: $NYT_NO_EMAIL"
echo "Lists: $NYT_LIST_NAMES"
echo "Catalog URL: $CATALOG_BASE_URL"
echo "Output dir: $NYT_OUTPUT_DIR"
echo "Log dir: $NYT_LOG_DIR"
echo "ChromeDriver: $CHROMEDRIVER_PATH"
echo "SMTP: $SMTP_SERVER:$SMTP_PORT"
echo "Recipients: $RECEIVER_EMAILS"
echo "================"

# --- SECTION 8: SCRIPT EXECUTION ---
# Resolve the Python script next to this runner (portable; no hardcoded absolute path)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT="${SCRIPT_DIR}/NYT-to-Library-CatKey-Generator.py"

if [[ ! -f "$SCRIPT" ]]; then
  echo "FATAL: script not found at $SCRIPT" >&2
  exit 1
fi

python3 -u "$SCRIPT"
code=$?

echo "=== Finished (exit $code) @ $(date -Is) ==="
exit $code
