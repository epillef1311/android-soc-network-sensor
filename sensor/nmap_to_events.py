#!/usr/bin/env python3

import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()

    if not value:
        fail(f"environment variable {name} is not configured")

    return value


def read_expected_hosts(path: Path) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        fail(f"could not read targets file: {exc}")

    hosts = []

    for line in lines:
        value = line.strip()

        if value and not value.startswith("#"):
            hosts.append(value)

    if not hosts:
        fail("targets file is empty")

    return list(dict.fromkeys(hosts))


def read_scan(xml_path: Path) -> tuple[dict[str, str], str]:
    try:
        root = ET.parse(xml_path).getroot()
    except (OSError, ET.ParseError) as exc:
        fail(f"could not parse Nmap XML: {exc}")

    detected = {}

    for host in root.findall("host"):
        status = host.find("status")
        address = host.find("address[@addrtype='ipv4']")

        if status is None or address is None:
            continue

        ip = address.get("addr")

        if ip:
            detected[ip] = status.get("reason") or "unknown"

    finished = root.find("./runstats/finished")
    timestamp = finished.get("time") if finished is not None else None

    try:
        observed_at = datetime.fromtimestamp(
            int(timestamp),
            tz=timezone.utc,
        ).isoformat()
    except (TypeError, ValueError, OSError):
        observed_at = datetime.now(timezone.utc).isoformat()

    return detected, observed_at


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Nmap discovery XML to SOC Collector NDJSON events."
    )
    parser.add_argument("xml_file", type=Path)
    parser.add_argument("targets_file", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    sensor_id = required_env("SENSOR_ID")
    network_id = required_env("NETWORK_ID")
    source = os.getenv("SOURCE", "android").strip() or "android"

    expected_hosts = read_expected_hosts(args.targets_file)
    detected, observed_at = read_scan(args.xml_file)

    events = []

    for ip in expected_hosts:
        is_up = ip in detected
        state = "up" if is_up else "down"
        reason = detected.get(ip, "no-response")

        event = {
            "event_type": "network.host.status",
            "sensor_id": sensor_id,
            "network_id": network_id,
            "observed_at": observed_at,
            "source": source,
            "data": {
                "message": f"Host {ip} is {state}",
                "ip": ip,
                "state": state,
                "reason": reason,
                "scan_type": "nmap_tcp_discovery",
            },
        }

        events.append(
            json.dumps(event, ensure_ascii=False, separators=(",", ":"))
        )

    output = "\n".join(events) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")


if __name__ == "__main__":
    main()
