#!/usr/bin/env bash
set -euo pipefail

# === Jacommi 푸시 자동 발송 (conda 환경용) ===
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

CONDA_ENV="Jacommi"
CONDA_BIN="/opt/anaconda3/bin/conda"   # conda 위치 확인 후 필요시 수정
LOG_FILE="$PROJECT_DIR/cron_push.log"

{
  echo "[INFO] $(date '+%F %T') push_today start"
  $CONDA_BIN run -n "$CONDA_ENV" python "$PROJECT_DIR/manage.py" push_today >> "$LOG_FILE" 2>&1
  echo "[INFO] $(date '+%F %T') push_today end"
  echo "----------------------------------------"
} >> "$LOG_FILE" 2>&1