#!/usr/bin/env python3
"""Write the lab queue definition; original /etc/asterisk must be backed up."""
import os
from pathlib import Path

os.umask(0o022)
path = Path("/etc/asterisk/queues.conf")
header = """; Call-center queue for the Asterisk/PJSIP test lab.
[general]
persistentmembers=no
autofill=yes

[cc]
strategy=rrmemory
timeout=20
retry=2
wrapuptime=3
maxlen=10
ringinuse=no
joinempty=paused,invalid,unavailable,unknown
leavewhenempty=paused,invalid,unavailable,unknown
musicclass=default

"""
members = "".join(
    f"member => PJSIP/{number},0,CC{number}\n"
    for number in range(3300, 3400)
)
path.write_text(header + members, encoding="utf-8")
path.chmod(0o644)
print(f"Wrote: {path} (queue cc, 100 static members)")
