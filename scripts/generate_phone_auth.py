#!/usr/bin/env python3
"""Create initial local PJSIP auth objects without replacing credentials."""

import argparse
import os
import secrets
from pathlib import Path


def create_auth_file(destination: Path) -> None:
    previous_umask = os.umask(0o077)
    try:
        destination.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with destination.open("x", encoding="utf-8") as config:
            for number in ("3000", "3001"):
                config.write(
                    f"[auth{number}]\n"
                    "type=auth\n"
                    "auth_type=digest\n"
                    f"username={number}\n"
                    f"password={secrets.token_hex(16)}\n\n"
                )
    finally:
        os.umask(previous_umask)
    print(f"Created: {destination}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("/etc/asterisk/local/pjsip-auth.conf"),
    )
    args = parser.parse_args()
    create_auth_file(args.output)


if __name__ == "__main__":
    main()
