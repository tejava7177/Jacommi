#!/usr/bin/env bash
set -euo pipefail

# === Jacommi 자동 생성 스크립트 (Conda 안전 버전) ===
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
CONDA_ENV="Jacommi"   # conda 환경 이름 (대소문자 주의)

LOG_FILE="$PROJECT_DIR/cron_generate.log"

# conda 존재 확인
if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] conda not found in PATH" | tee -a "$LOG_FILE"
  exit 1
fi

cd "$PROJECT_DIR"

# Conda 환경으로 실행 (.env는 manage.py에서 load_dotenv()로 로드)
echo "[INFO] $(date '+%F %T') generate_daily_set args: $*" >> "$LOG_FILE"
conda run -n "$CONDA_ENV" python manage.py generate_daily_set "$@" >> "$LOG_FILE" 2>&1