#!/bin/bash
# ============================================================================
# run_nyt_script.sh
# Robust runner for NYT-to-Library-CatKey-Generator
# ============================================================================
# It loads secrets from a local `.env` file which should be in your .gitignore.
# ============================================================================

set -euo pipefail

# --- SECTION 1: LOAD ENVIRONMENT SECRETS ---
# This block looks for a local `.env` file and loads it if it exists.
if [ -f .env ]; then
  echo "Loading environment variables from .env file..."
  source .env
else
  echo "INFO: .env file not found. Relying on externally set environment variables."
fi

# --- SECTION 2: INITIALIZE DEFAULTS ---
NYT_DEBUG="${NYT_DEBUG:-0}"
LISTS_OVERRIDE=""
NO_EMAIL=0

# --- SECTION 3: PARSE COMMAND-LINE ARGUMENTS ---
while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug)      NYT_DEBUG=1; shift;;
    --no-debug)   NYT_DEBUG=0; shift;;
    --lists)      LISTS_OVERRIDE="$2"; shift 2;;
    --no-email)   NO_EMAIL=1; shift;;
    --quick-test) LISTS_OVERRIDE="hardcover-fiction"; shift;;
    *) echo "Unknown option: $1" >&2; exit 2;;
  esac
done

# --- SECTION 4: SET UP ENVIRONMENT VARIABLES ---
# NOTE: Secrets are no longer defined here. They are loaded from the .env file.

# --- Other Settings (safe to keep defaults) ---
export SMTP_SERVER="${SMTP_SERVER:-smtp.gmail.com}"
export SMTP_PORT="${SMTP_PORT:-587}"

DEFAULT_LISTS="hardcover-fiction,hardcover-nonfiction,picture-books,childrens-middle-grade-hardcover,young-adult-hardcover"
if [[ -n "$LISTS_OVERRIDE" ]]; then
  export NYT_LIST_NAMES="$LISTS_OVERRIDE"
else
  export NYT_LIST_NAMES="${NYT_LIST_NAMES:-$DEFAULT_LISTS}"
fi

export NYT_OUTPUT_DIR="${NYT_OUTPUT_DIR:-$HOME/catkey_exports}"
export NYT_LOG_DIR="${NYT_LOG_DIR:-$HOME/logs}"
export CHROMEDRIVER_PATH="${CHROMEDRIVER_PATH:-/usr/local/bin/chromedriver}"
export NYT_DEBUG
export PYTHONUNBUFFERED=1
export NYT_NO_EMAIL="$NO_EMAIL"

# --- SECTION 5: SANITY CHECKS ---
# This section now becomes more important as it verifies that secrets were loaded correctly.
missing=()
[[ -z "${SENDER_EMAIL:-}"    ]] && missing+=("SENDER_EMAIL")
[[ -z "${SENDER_PASSWORD:-}" ]] && missing+=("SENDER_PASSWORD")
[[ -z "${RECEIVER_EMAILS:-}" ]] && missing+=("RECEIVER_EMAILS")
[[ -z "${NYT_API_KEY:-}"     ]] && missing+=("NYT_API_KEY")
if (( ${#missing[@]} > 0 )); then
  echo "FATAL: missing env vars: ${missing[*]}" >&2
  echo "Hint: Make sure you have created a '.env' file with your secrets." >&2
  exit 1
fi
mkdir -p "$NYT_OUTPUT_DIR" "$NYT_LOG_DIR"

# --- SECTION 6: STARTUP SUMMARY ---
echo "=== Startup ==="
echo "Time: $(date -Is)"
echo "Debug (NYT_DEBUG): $NYT_DEBUG"
echo "No email: $NO_EMAIL"
echo "Lists: $NYT_LIST_NAMES"
# For security, we don't print passwords or API keys to the log.
echo "Sender: $SENDER_EMAIL"
echo "================"

# --- SECTION 7: SCRIPT EXECUTION ---
SCRIPT="/home/systemslibrarian/NYT-to-Library-CatKey-Generator.py"
if [[ ! -f "$SCRIPT" ]]; then
  echo "FATAL: script not found at $SCRIPT" >&2
  exit 1
fi
python3 -u "$SCRIPT"
code=$?
echo "=== Finished (exit $code) @ $(date -Is) ==="
exit $code
