#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# run_nyt_script.sh — Runner for NYT→CatKey (single catalog)
# ─────────────────────────────────────────────────────────────────────────────
# Usage examples:
#   ./run_nyt_script.sh --env ./nyt_catkey.env --debug
#   ./run_nyt_script.sh --quick-test --no-email
#
set -euo pipefail

NYT_DEBUG="${NYT_DEBUG:-0}"
LISTS_OVERRIDE=""
NO_EMAIL=0
ENV_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --debug) NYT_DEBUG=1; shift;;
    --no-debug) NYT_DEBUG=0; shift;;
    --lists) LISTS_OVERRIDE="$2"; shift 2;;
    --no-email) NO_EMAIL=1; shift;;
    --quick-test) LISTS_OVERRIDE="hardcover-fiction"; shift;;
    --env) ENV_FILE="$2"; shift 2;;
    *) echo "Unknown option: $1" >&2; exit 2;;
  esac
done

# Optional .env loading
if [[ -n "$ENV_FILE" ]]; then
  if [[ -f "$ENV_FILE" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
  else
    echo "WARN: --env file not found: $ENV_FILE" >&2
  fi
fi

# Required secrets (no hardcoded defaults here)
: "${SENDER_EMAIL:?Set SENDER_EMAIL}"
: "${SENDER_PASSWORD:?Set SENDER_PASSWORD}"
: "${RECEIVER_EMAILS:?Set RECEIVER_EMAILS}"
: "${NYT_API_KEY:?Set NYT_API_KEY}"
: "${CATALOG_BASE_URL:?Set CATALOG_BASE_URL}"

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

mkdir -p "$NYT_OUTPUT_DIR" "$NYT_LOG_DIR"

echo "=== Startup ==="
echo "Time: $(date -Is)"
echo "Debug (NYT_DEBUG): $NYT_DEBUG"
echo "No email: $NO_EMAIL"
echo "Lists: $NYT_LIST_NAMES"
echo "Catalog: $CATALOG_BASE_URL"
echo "Output dir: $NYT_OUTPUT_DIR"
echo "Log dir: $NYT_LOG_DIR"
echo "ChromeDriver: $CHROMEDRIVER_PATH"
echo "SMTP: $SMTP_SERVER:$SMTP_PORT"
echo "Recipients: $RECEIVER_EMAILS"
echo "================"

SCRIPT="$(dirname "$0")/nyt_catkey_enhanced.py"
if [[ ! -f "$SCRIPT" ]]; then
  SCRIPT="/mnt/data/nyt_catkey_enhanced.py"
fi

python3 -u "$SCRIPT"; code=$?
echo "=== Finished (exit $code) @ $(date -Is) ==="
exit $code
