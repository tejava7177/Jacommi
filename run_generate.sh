#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
CONDA_ENV="Jacommi"
LOG_FILE="$PROJECT_DIR/cron_generate.log"

# 진단 로그
{
  echo "[INFO] $(date '+%F %T') generate_daily_set args: $*"
  echo "[INFO] USER=$(id -un) PWD=$PWD"
  echo "[INFO] USING_CONDA_BIN=/opt/anaconda3/bin/conda"
  echo "[INFO] PATH=$PATH"
} >> "$LOG_FILE"

cd "$PROJECT_DIR"
/opt/anaconda3/bin/conda run -n "$CONDA_ENV" python manage.py generate_daily_set "$@" >> "$LOG_FILE" 2>&1