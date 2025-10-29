#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List

CONFIG_PATH = Path(os.environ.get("XRAY_CONFIG_PATH", "/etc/xray/config.json"))

MARKERS: Dict[str, Dict[str, str]] = {
    "vmess": {
        "anchor": "#vmess",
        "prefix": "###",
        "id_key": "id",
        "entry_prefix": "},{",
        "body_template": '"id": "{identifier}","alterId": 0,"email": "{name}"',
    },
    "vless": {
        "anchor": "#vless",
        "prefix": "#&",
        "id_key": "id",
        "entry_prefix": "},{",
        "body_template": '"id": "{identifier}","email": "{name}"',
    },
    "trojan": {
        "anchor": "#trojanws",
        "prefix": "#!",
        "id_key": "password",
        "entry_prefix": "},{",
        "body_template": '"password": "{identifier}","email": "{name}"',
    },
}


def load_lines() -> List[str]:
    if not CONFIG_PATH.exists():
        raise SystemExit(f"Config not found: {CONFIG_PATH}")
    return CONFIG_PATH.read_text().splitlines()


def save_lines(lines: List[str]) -> None:
    CONFIG_PATH.write_text("\n".join(lines) + "\n")


def ensure_unique(kind: str, name: str, lines: List[str]) -> None:
    prefix = MARKERS[kind]["prefix"]
    target = name.lower()
    for line in lines:
        if line.startswith(prefix):
            parts = line.split()
            if len(parts) >= 2 and parts[1].lower() == target:
                raise SystemExit(f"Account '{name}' already exists for {kind}")


def add_account(kind: str, name: str, identifier: str, expiry: str) -> None:
    lines = load_lines()
    ensure_unique(kind, name, lines)

    data = MARKERS[kind]
    anchor = data["anchor"]
    comment_line = f"{data['prefix']} {name} {expiry}"
    entry_line = f"{data['entry_prefix']}{data['body_template'].format(identifier=identifier, name=name)}"

    new_lines: List[str] = []
    inserted = False

    for line in lines:
        if not inserted and line.strip() == anchor:
            new_lines.append(comment_line)
            new_lines.append(entry_line)
            inserted = True
        new_lines.append(line)

    if not inserted:
        raise SystemExit(f"Anchor '{anchor}' not found in config")

    save_lines(new_lines)


def delete_account(kind: str, name: str) -> None:
    lines = load_lines()
    data = MARKERS[kind]
    prefix = data["prefix"]
    target = name.lower()

    new_lines: List[str] = []
    i = 0
    removed = False

    while i < len(lines):
        line = lines[i]
        if line.startswith(prefix):
            parts = line.split()
            if len(parts) >= 2 and parts[1].lower() == target:
                removed = True
                i += 1  # skip comment
                if i < len(lines) and lines[i].lstrip().startswith(data["entry_prefix"]):
                    i += 1  # skip entry json line
                continue
        new_lines.append(line)
        i += 1

    if not removed:
        raise SystemExit(f"Account '{name}' not found for {kind}")

    save_lines(new_lines)


def renew_account(kind: str, name: str, new_expiry: str) -> None:
    lines = load_lines()
    prefix = MARKERS[kind]["prefix"]
    target = name.lower()
    updated = False
    new_lines: List[str] = []

    for line in lines:
        if line.startswith(prefix):
            parts = line.split()
            if len(parts) >= 2 and parts[1].lower() == target:
                original_name = parts[1]
                new_lines.append(f"{prefix} {original_name} {new_expiry}")
                updated = True
                continue
        new_lines.append(line)

    if not updated:
        raise SystemExit(f"Account '{name}' not found for {kind}")

    save_lines(new_lines)


def list_accounts(kind: str) -> None:
    lines = load_lines()
    prefix = MARKERS[kind]["prefix"]
    id_key = MARKERS[kind]["id_key"]
    anchor = MARKERS[kind]["anchor"]
    results: List[Dict[str, str]] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == anchor:
            i += 1
            continue

        if line.startswith(prefix):
            parts = line.split()
            name = parts[1] if len(parts) >= 2 else ""
            expiry = parts[2] if len(parts) >= 3 else ""
            identifier_line = lines[i + 1] if i + 1 < len(lines) else ""
            pattern = rf'"{id_key}":\s*"([^"]+)"'
            match = re.search(pattern, identifier_line)
            identifier = match.group(1) if match else ""
            results.append({"name": name, "expiry": expiry, "id": identifier})
        i += 1

    print(json.dumps(results, indent=2))


def exists_account(kind: str, name: str) -> bool:
    lines = load_lines()
    prefix = MARKERS[kind]["prefix"]
    target = name.lower()
    for line in lines:
        if line.startswith(prefix):
            parts = line.split()
            if len(parts) >= 2 and parts[1].lower() == target:
                return True
    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Xray account manager helper.")
    parser.add_argument("action", choices=["add", "delete", "renew", "list", "exists"])
    parser.add_argument("--kind", choices=list(MARKERS.keys()), required=True)
    parser.add_argument("--name")
    parser.add_argument("--identifier")
    parser.add_argument("--expiry")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.action == "add":
        if not all([args.name, args.identifier, args.expiry]):
            raise SystemExit("add action needs --name, --identifier, --expiry")
        add_account(args.kind, args.name, args.identifier, args.expiry)
    elif args.action == "delete":
        if not args.name:
            raise SystemExit("delete action needs --name")
        delete_account(args.kind, args.name)
    elif args.action == "renew":
        if not (args.name and args.expiry):
            raise SystemExit("renew action needs --name and --expiry")
        renew_account(args.kind, args.name, args.expiry)
    elif args.action == "list":
        list_accounts(args.kind)
    elif args.action == "exists":
        if not args.name:
            raise SystemExit("exists action needs --name")
        sys.exit(0 if exists_account(args.kind, args.name) else 1)


if __name__ == "__main__":
    main()
