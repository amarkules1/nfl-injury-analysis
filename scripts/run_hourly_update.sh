#!/usr/bin/env bash
# ==============================================================================
# NFL Injury Analysis - Hourly Update Automation Script for Ubuntu
# ==============================================================================
# Usage:
#   ./scripts/run_hourly_update.sh [OUTPUT_DIR]
#
# Environment overrides:
#   TARGET_OUTPUT_DIR : Target folder for data file exports
#   LOG_DIR           : Directory to store execution logs
#   SEASON            : NFL season year (defaults to current season in config)
# ==============================================================================

set -euo pipefail

# Determine script and project directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# Ensure common binary paths are in PATH (critical for cron environments)
export PATH="/home/${USER:-ubuntu}/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:${PATH}"

# Configuration
TARGET_OUTPUT_DIR="${1:-${TARGET_OUTPUT_DIR:-/var/data/nfl-injuries}}"
LOG_DIR="${LOG_DIR:-${PROJECT_ROOT}/logs}"
LOG_FILE="${LOG_DIR}/hourly_update_$(date +'%Y%m%d').log"
LOCK_FILE="/tmp/nfl_injury_hourly_update.lock"
SEASON="${SEASON:-2026}"

# Ensure directories exist
mkdir -p "${TARGET_OUTPUT_DIR}"
mkdir -p "${LOG_DIR}"

# Execute under a non-blocking lock to prevent overlapping runs
exec 200>"${LOCK_FILE}"
if ! flock -n 200; then
    echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Previous update run is still in progress. Skipping this cycle." >> "${LOG_FILE}"
    exit 0
fi

# Log start
echo "================================================================================" >> "${LOG_FILE}"
echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] Starting NFL Injury Hourly Update" >> "${LOG_FILE}"
echo "  Project Root: ${PROJECT_ROOT}" >> "${LOG_FILE}"
echo "  Target Output: ${TARGET_OUTPUT_DIR}" >> "${LOG_FILE}"
echo "  Season:        ${SEASON}" >> "${LOG_FILE}"
echo "================================================================================" >> "${LOG_FILE}"

cd "${PROJECT_ROOT}"

# Run update pipeline via Pipenv
if command -v pipenv3.10 >/dev/null 2>&1; then
    pipenv3.10 run python3.10 update_injury_log.py \
        --season "${SEASON}" \
        --output-dir "${TARGET_OUTPUT_DIR}" \
        >> "${LOG_FILE}" 2>&1
else
    # Fallback to python3 directly if pipenv is not in PATH
    python3.10 update_injury_log.py \
        --season "${SEASON}" \
        --output-dir "${TARGET_OUTPUT_DIR}" \
        >> "${LOG_FILE}" 2>&1
fi

echo "[$(date -u +'%Y-%m-%dT%H:%M:%SZ')] NFL Injury Hourly Update completed successfully." >> "${LOG_FILE}"

