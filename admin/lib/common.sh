#!/bin/bash

set -euo pipefail

ADMIN_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT="${PROJECT_ROOT_OVERRIDE:-$(cd "${ADMIN_DIR}/../.." && pwd)}"
DATA_DIR="${PROJECT_ROOT}/data"
DB_PATH="${DATA_DIR}/app.db"

HELPER_PY="${ADMIN_DIR}/profiles.py"

ensure_cmd() {
    local cmd="$1"
    command -v "$cmd" >/dev/null 2>&1 || { echo "Perintah '$cmd' dibutuhkan." >&2; exit 1; }
}

ensure_python() {
    ensure_cmd python3
}

run_helper() {
    ensure_python
    PROJECT_ROOT="$PROJECT_ROOT" python3 "$HELPER_PY" "$@"
}

heading() {
    local title="$1"
    echo "============================================"
    printf " %s\n" "$title"
    echo "============================================"
}
