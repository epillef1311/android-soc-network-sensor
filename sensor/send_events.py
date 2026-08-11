#!/usr/bin/env python3

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def log(log_file: Path, message: str) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    entry = f"{timestamp} {message}"

    print(entry)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    with log_file.open("a", encoding="utf-8") as file:
        file.write(entry + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send NDJSON events to the SOC Collector."
    )
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--start-line", type=int, default=1)
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path.home() / "soc-sensor/logs/event-send.log",
    )
    args = parser.parse_args()

    api_url = os.getenv("API_URL", "").strip().rstrip("/")
    token = os.getenv("SOC_COLLECTOR_TOKEN", "").strip()

    if not api_url:
        print("error: API_URL is not configured", file=sys.stderr)
        return 1

    if not token:
        print("error: SOC_COLLECTOR_TOKEN is not configured", file=sys.stderr)
        return 1

    try:
        lines = args.input_file.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        print(f"error: could not read input file: {exc}", file=sys.stderr)
        return 1

    successes = 0
    failures = 0

    for line_number, raw_line in enumerate(lines, start=1):
        if line_number < args.start_line or not raw_line.strip():
            continue

        try:
            event = json.loads(raw_line)
            payload = json.dumps(
                event,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        except (json.JSONDecodeError, TypeError) as exc:
            failures += 1
            log(
                args.log_file,
                f"FAIL line={line_number} reason=invalid-json error={exc}",
            )
            continue

        ip = event.get("data", {}).get("ip", "unknown")

        request = urllib.request.Request(
            f"{api_url}/events",
            data=payload,
            method="POST",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                response_body = response.read().decode("utf-8")
                result = json.loads(response_body)
                status_code = response.status
                event_id = result.get("event_id", "unknown")

                if status_code == 202:
                    successes += 1
                    log(
                        args.log_file,
                        f"OK line={line_number} ip={ip} "
                        f"http={status_code} event_id={event_id}",
                    )
                else:
                    failures += 1
                    log(
                        args.log_file,
                        f"FAIL line={line_number} ip={ip} http={status_code}",
                    )

        except urllib.error.HTTPError as exc:
            failures += 1
            log(
                args.log_file,
                f"FAIL line={line_number} ip={ip} http={exc.code}",
            )

        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            failures += 1
            log(
                args.log_file,
                f"FAIL line={line_number} ip={ip} error={exc}",
            )

    log(
        args.log_file,
        f"SUMMARY success={successes} failure={failures}",
    )

    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
