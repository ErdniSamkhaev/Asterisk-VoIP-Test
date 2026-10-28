#!/usr/bin/env python3
"""Create endpoint and AoR definitions for all call-center extensions."""
import os
from pathlib import Path

os.umask(0o022)
path = Path("/etc/asterisk/pjsip-cc.conf")
with path.open("x", encoding="utf-8") as config:
    config.write("; Call-center extensions 3300-3399. Uses phone templates.\n")
    for number in range(3300, 3400):
        config.write(
            f"[{number}](phone-endpoint)\n"
            f"auth=auth{number}\n"
            f"aors={number}\n"
            f"callerid=CC {number} <{number}>\n\n"
            f"[{number}](phone-aor)\n\n"
        )
print(f"Created: {path} (100 endpoints, 100 AoRs)")
