#!/usr/bin/env python3
"""Create local call-center credentials once; run as root on Linux."""
import grp
import os
import secrets
from pathlib import Path

os.umask(0o027)
group_id = grp.getgrnam("asterisk").gr_gid
path = Path("/etc/asterisk/local/pjsip-auth-cc.conf")
with path.open("x", encoding="utf-8") as config:
    os.fchown(config.fileno(), -1, group_id)
    for number in range(3300, 3400):
        config.write(
            f"[auth{number}]\n"
            "type=auth\n"
            "auth_type=digest\n"
            f"username={number}\n"
            f"password={secrets.token_hex(16)}\n\n"
        )
print(f"Created: {path} (100 auth objects; root:asterisk, mode 640)")
