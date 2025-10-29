#!/usr/bin/env python3
import argparse
import json
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

try:  # Python 3.11+
    from datetime import UTC  # type: ignore[attr-defined]
except ImportError:  # Python 3.10 fallback
    UTC = timezone.utc

PROJECT_ROOT = Path(
    os.environ.get(
        "PROJECT_ROOT",
        os.environ.get("PROJECT_ROOT_OVERRIDE", Path(__file__).resolve().parents[2]),
    )
)
DB_PATH = PROJECT_ROOT / "data" / "app.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE COLLATE NOCASE,
                domain TEXT NOT NULL,
                ssh_port INTEGER NOT NULL,
                cpu_percent INTEGER NOT NULL,
                ram_mb INTEGER NOT NULL,
                password TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                bandwidth_limit_tb REAL NOT NULL,
                bandwidth_used_tb REAL DEFAULT 0,
                restore_link TEXT,
                status TEXT DEFAULT 'pending',
                container_name TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TRIGGER IF NOT EXISTS trg_profiles_updated
            AFTER UPDATE ON profiles
            BEGIN
                UPDATE profiles
                SET updated_at = datetime('now')
                WHERE id = NEW.id;
            END;
            """
        )


def create_profile(data: Dict[str, Any]) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO profiles
                (name, domain, ssh_port, cpu_percent, ram_mb, password, expires_at,
                 bandwidth_limit_tb, bandwidth_used_tb, restore_link, status, container_name)
            VALUES
                (:name, :domain, :ssh_port, :cpu_percent, :ram_mb, :password, :expires_at,
                 :bandwidth_limit_tb, :bandwidth_used_tb, :restore_link, :status, :container_name)
            """,
            data,
        )


def list_profiles() -> List[Dict[str, Any]]:
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT *,
                   CAST((julianday(expires_at) - julianday('now')) AS INTEGER) AS remaining_days,
                   bandwidth_limit_tb - bandwidth_used_tb AS remaining_bandwidth_tb
            FROM profiles
            ORDER BY name COLLATE NOCASE
            """
        ).fetchall()
    return [dict(row) for row in rows]


def get_profile(name: str) -> Dict[str, Any]:
    init_db()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM profiles WHERE name = ? COLLATE NOCASE",
            (name,),
        ).fetchone()
        if not row:
            raise SystemExit(f"Profile '{name}' tidak ditemukan.")
    return dict(row)


def delete_profile(name: str) -> None:
    init_db()
    with get_connection() as conn:
        cur = conn.execute(
            "DELETE FROM profiles WHERE name = ? COLLATE NOCASE",
            (name,),
        )
        if cur.rowcount == 0:
            raise SystemExit(f"Profile '{name}' tidak ditemukan.")


def extend_days(name: str, days: int) -> Dict[str, Any]:
    profile = get_profile(name)
    current_expiry = datetime.strptime(profile["expires_at"], "%Y-%m-%d")
    today = datetime.now(UTC).date()
    base_date = max(current_expiry.date(), today)
    new_expiry = base_date + timedelta(days=days)
    with get_connection() as conn:
        conn.execute(
            "UPDATE profiles SET expires_at = ? WHERE name = ? COLLATE NOCASE",
            (new_expiry.isoformat(), name),
        )
    profile["expires_at"] = new_expiry.isoformat()
    return profile


def extend_bandwidth(name: str, increment: float) -> Dict[str, Any]:
    profile = get_profile(name)
    new_limit = float(profile["bandwidth_limit_tb"]) + increment
    with get_connection() as conn:
        conn.execute(
            "UPDATE profiles SET bandwidth_limit_tb = ? WHERE name = ? COLLATE NOCASE",
            (new_limit, name),
        )
    profile["bandwidth_limit_tb"] = new_limit
    return profile


def update_status(name: str, status: str, container_name: str = None) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            "UPDATE profiles SET status = ?, container_name = COALESCE(?, container_name) WHERE name = ? COLLATE NOCASE",
            (status, container_name, name),
        )


def update_bandwidth(name: str, used_tb: float) -> None:
    init_db()
    with get_connection() as conn:
        conn.execute(
            "UPDATE profiles SET bandwidth_used_tb = ? WHERE name = ? COLLATE NOCASE",
            (used_tb, name),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile manager helper")
    parser.add_argument("action", choices=["init", "create", "list", "detail", "delete", "extend_days", "extend_bw", "status", "usage"])
    parser.add_argument("--name")
    parser.add_argument("--domain")
    parser.add_argument("--ssh_port", type=int)
    parser.add_argument("--cpu_percent", type=int)
    parser.add_argument("--ram_mb", type=int)
    parser.add_argument("--password")
    parser.add_argument("--expires_at")
    parser.add_argument("--bandwidth_limit_tb", type=float)
    parser.add_argument("--restore_link")
    parser.add_argument("--status_value")
    parser.add_argument("--container_name")
    parser.add_argument("--days", type=int)
    parser.add_argument("--increment", type=float)
    parser.add_argument("--used_tb", type=float)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.action == "init":
        init_db()
        return

    if args.action == "create":
        required = ["name", "domain", "ssh_port", "cpu_percent", "ram_mb", "password", "expires_at", "bandwidth_limit_tb"]
        for field in required:
            if getattr(args, field) is None:
                raise SystemExit(f"Parameter --{field} wajib diisi.")
        data = {
            "name": args.name,
            "domain": args.domain,
            "ssh_port": args.ssh_port,
            "cpu_percent": args.cpu_percent,
            "ram_mb": args.ram_mb,
            "password": args.password,
            "expires_at": args.expires_at,
            "bandwidth_limit_tb": args.bandwidth_limit_tb,
            "bandwidth_used_tb": 0.0,
            "restore_link": args.restore_link,
            "status": "pending",
            "container_name": None,
        }
        create_profile(data)
        return

    if args.action == "list":
        print(json.dumps(list_profiles(), indent=2))
        return

    if args.action == "detail":
        if not args.name:
            raise SystemExit("--name dibutuhkan untuk detail.")
        print(json.dumps(get_profile(args.name), indent=2))
        return

    if args.action == "delete":
        if not args.name:
            raise SystemExit("--name dibutuhkan untuk delete.")
        delete_profile(args.name)
        return

    if args.action == "extend_days":
        missing = []
        if not args.name:
            missing.append("--name")
        if args.days is None:
            missing.append("--days")
        if missing:
            raise SystemExit(f"{' dan '.join(missing)} dibutuhkan.")
        result = extend_days(args.name, args.days)
        print(json.dumps(result, indent=2))
        return

    if args.action == "extend_bw":
        missing = []
        if not args.name:
            missing.append("--name")
        if args.increment is None:
            missing.append("--increment")
        if missing:
            raise SystemExit(f"{' dan '.join(missing)} dibutuhkan.")
        result = extend_bandwidth(args.name, args.increment)
        print(json.dumps(result, indent=2))
        return

    if args.action == "status":
        missing = []
        if not args.name:
            missing.append("--name")
        if not args.status_value:
            missing.append("--status_value")
        if missing:
            raise SystemExit(f"{' dan '.join(missing)} dibutuhkan.")
        update_status(args.name, args.status_value, args.container_name)
        return

    if args.action == "usage":
        missing = []
        if not args.name:
            missing.append("--name")
        if args.used_tb is None:
            missing.append("--used_tb")
        if missing:
            raise SystemExit(f"{' dan '.join(missing)} dibutuhkan.")
        update_bandwidth(args.name, args.used_tb)
        return


if __name__ == "__main__":
    main()
