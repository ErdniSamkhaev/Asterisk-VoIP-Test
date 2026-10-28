#!/usr/bin/env python3
"""Create a local AMI account for the TP sync script; run as root."""
import grp
import os
import secrets
from pathlib import Path

if os.geteuid() != 0:
    raise SystemExit("Run as root")
os.umask(0o027)
group_id = grp.getgrnam("asterisk").gr_gid
path = Path("/etc/asterisk/local/manager-tp.conf")
with path.open("x", encoding="utf-8") as config:
    os.fchown(config.fileno(), -1, group_id)
    config.write(
        "[tp-sync]\n"
        f"secret={secrets.token_hex(32)}\n"
        "deny=0.0.0.0/0.0.0.0\n"
        "permit=127.0.0.1/255.255.255.255\n"
        "read=system\n"
        "write=system\n"
    )
print(f"Created: {path} (root:asterisk, mode 640)")
