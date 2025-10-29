#!/bin/bash

# Utility functions for managing services inside Docker-friendly environments.
# Prefer supervisorctl when available; fall back to simple process checks.

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

SUPERVISORCTL_BIN="${SUPERVISORCTL_BIN:-$(command -v supervisorctl)}"

service_restart() {
    local svc="$1"
    if [[ -n "$SUPERVISORCTL_BIN" ]]; then
        $SUPERVISORCTL_BIN restart "$svc" >/dev/null 2>&1 && return 0
        $SUPERVISORCTL_BIN start "$svc" >/dev/null 2>&1 && return 0
        echo "WARN: supervisorctl gagal me-restart $svc" >&2
        return 1
    fi

    # Fallback: coba hentikan proses, lalu jalankan ulang jika ada script start.
    pkill -f "$svc" >/dev/null 2>&1 || true
    if command_exists "$svc"; then
        "$svc" >/dev/null 2>&1 &
        disown
        return 0
    fi

    echo "WARN: Tidak ada mekanisme restart untuk $svc (butuh supervisorctl)" >&2
    return 1
}

service_status() {
    local svc="$1"
    if [[ -n "$SUPERVISORCTL_BIN" ]]; then
        local output
        output=$($SUPERVISORCTL_BIN status "$svc" 2>/dev/null)
        if grep -qE "\bRUNNING\b" <<<"$output"; then
            echo "Running"
        elif grep -qE "\bSTOPPED\b|\bEXITED\b" <<<"$output"; then
            echo "Stopped"
        else
            echo "Unknown"
        fi
        return
    fi

    if pgrep -f "$svc" >/dev/null 2>&1; then
        echo "Running"
    else
        echo "Stopped"
    fi
}

service_ensure_running() {
    local svc="$1"
    if [[ -n "$SUPERVISORCTL_BIN" ]]; then
        $SUPERVISORCTL_BIN start "$svc" >/dev/null 2>&1 || true
        return
    fi

    if ! pgrep -f "$svc" >/dev/null 2>&1 && command_exists "$svc"; then
        "$svc" >/dev/null 2>&1 &
        disown
    fi
}

service_stop() {
    local svc="$1"
    if [[ -n "$SUPERVISORCTL_BIN" ]]; then
        $SUPERVISORCTL_BIN stop "$svc" >/dev/null 2>&1 && return 0
        echo "WARN: supervisorctl gagal menghentikan $svc" >&2
        return 1
    fi
    pkill -f "$svc" >/dev/null 2>&1 || true
}
