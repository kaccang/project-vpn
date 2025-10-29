#!/usr/bin/env bash

set -euo pipefail

log() {
    printf '[project-vpn] %s\n' "$*"
}

fail() {
    printf '[project-vpn][error] %s\n' "$*" >&2
    exit 1
}

need_root() {
    if [[ ${INSTALL_ALLOW_NON_ROOT:-0} -eq 1 ]]; then
        return
    fi
    if [[ $EUID -ne 0 ]]; then
        fail "Harus dijalankan sebagai root atau gunakan sudo."
    fi
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || fail "Perintah '$1' tidak ditemukan."
}

fetch_repo() {
    local repo_url="$1"
    local branch="$2"
    local install_dir="$3"

    if [[ -d "$install_dir/.git" ]]; then
        log "Repositori sudah ada, melakukan pembaruan..."
        git -C "$install_dir" fetch --depth 1 origin "$branch"
        git -C "$install_dir" reset --hard "origin/$branch"
    else
        log "Mengkloning repositori $repo_url (branch: $branch)..."
        git clone --depth 1 -b "$branch" "$repo_url" "$install_dir"
    fi
}

install_packages() {
    local packages=("$@")
    if [[ ${INSTALL_SKIP_APT:-0} -eq 1 ]]; then
        log "Melewati instalasi paket (INSTALL_SKIP_APT=1)."
        return
    fi
    require_command apt-get
    log "Memperbarui paket apt..."
    apt-get update -y
    log "Menginstal dependensi: ${packages[*]}"
    DEBIAN_FRONTEND=noninteractive apt-get install -y "${packages[@]}"
}

ensure_directory() {
    local dir="$1"
    mkdir -p "$dir"
}

setup_permissions() {
    local dir="$1"
    chmod +x "$dir"/*.sh 2>/dev/null || true
    chmod +x "$dir"/script/* 2>/dev/null || true
    chmod +x "$dir"/admin/* 2>/dev/null || true
    chmod +x "$dir"/tests/*.sh 2>/dev/null || true
}

init_database() {
    local dir="$1"
    log "Inisialisasi database profil..."
    PROJECT_ROOT_OVERRIDE="$dir" python3 "$dir/admin/lib/profiles.py" init
}

create_symlink() {
    local target="$1"
    local link_path="$2"
    if [[ ${INSTALL_NO_SYMLINK:-0} -eq 1 ]]; then
        log "Melewati pembuatan symlink $link_path (INSTALL_NO_SYMLINK=1)."
        return
    fi
    ensure_directory "$(dirname "$link_path")"
    ln -sf "$target" "$link_path"
    chmod +x "$link_path"
}

write_profile_snippet() {
    local install_dir="$1"
    local snippet="/etc/profile.d/project-vpn.sh"
    if [[ ${INSTALL_NO_SYMLINK:-0} -eq 1 || ${INSTALL_NO_PROFILE_SNIPPET:-0} -eq 1 ]]; then
        log "Melewati pembuatan snippet profile (INSTALL_NO_SYMLINK/INSTALL_NO_PROFILE_SNIPPET disetel)."
        return
    fi
    cat <<EOF > "$snippet"
# project-vpn convenience shortcuts
if [ -d "$install_dir" ]; then
    alias project-vpn-admin="$install_dir/admin/menu-profile"
fi
EOF
}

print_summary() {
    local install_dir="$1"
    cat <<EOF

====================
Project VPN Terpasang
====================
Direktori  : $install_dir
Menu admin : project-vpn-admin (atau jalankan $install_dir/admin/menu-profile)

Langkah selanjutnya:
1. Gunakan perintah di atas untuk membuka dashboard admin.
2. Tambah profile/container baru melalui menu.
3. Masuk ke container (menu login) untuk menyelesaikan instalasi paket Xray/nginx jika diperlukan.

Catatan:
- Token Telegram dan kredensial lainnya perlu diatur manual di file konfigurasi terkait.
- Gunakan 'tests/run_tests.sh' untuk memverifikasi fungsi dasar (opsional).
EOF
}

main() {
    need_root

    : "${INSTALL_DIR:=/opt/project-vpn}"
    : "${INSTALL_REPO:=https://github.com/kaccang/project-vpn.git}"
    : "${INSTALL_BRANCH:=main}"

    local packages=(git curl jq python3 python3-venv python3-pip sqlite3 supervisor docker.io)

    log "Memulai proses instalasi Project VPN..."

    install_packages "${packages[@]}"

    if [[ ${INSTALL_SKIP_GIT:-0} -eq 1 ]]; then
        log "Melewati kloning repo (INSTALL_SKIP_GIT=1)."
        [[ -d "$INSTALL_DIR" ]] || fail "INSTALL_SKIP_GIT=1 tetapi direktori $INSTALL_DIR tidak ditemukan."
    else
        ensure_directory "$(dirname "$INSTALL_DIR")"
        fetch_repo "$INSTALL_REPO" "$INSTALL_BRANCH" "$INSTALL_DIR"
    fi

    cd "$INSTALL_DIR"

    setup_permissions "$INSTALL_DIR"
    init_database "$INSTALL_DIR"

    create_symlink "$INSTALL_DIR/admin/menu-profile" "/usr/local/bin/project-vpn-admin"
    create_symlink "$INSTALL_DIR/script/menu" "/usr/local/bin/project-vpn-menu"
    write_profile_snippet "$INSTALL_DIR"

    log "Instalasi selesai."
    print_summary "$INSTALL_DIR"
}

main "$@"
