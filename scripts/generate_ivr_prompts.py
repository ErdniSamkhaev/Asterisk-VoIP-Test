#!/usr/bin/env python3
"""Generate three Russian IVR prompts; run as root on Linux."""
import grp
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

espeak = shutil.which("espeak-ng")
sox = shutil.which("sox") or shutil.which("sox_ng")
if not espeak or not sox:
    raise SystemExit("Required tools not found: espeak-ng and sox/sox_ng")
if os.geteuid() != 0:
    raise SystemExit("Run as root")

prompts = {
    "ivr-welcome": "Здравствуйте. Наберите четырёхзначный добавочный номер сотрудника или дождитесь ответа оператора.",
    "ivr-invalid": "Номер набран неверно. Попробуйте ещё раз.",
    "ivr-unavailable": "К сожалению, сейчас все сотрудники недоступны. Пожалуйста, перезвоните позднее.",
}
directory = Path("/var/lib/asterisk/sounds/custom")
if any((directory / f"{name}.wav").exists() for name in prompts):
    raise SystemExit("An IVR output file already exists; nothing overwritten")

os.umask(0o027)
group_id = grp.getgrnam("asterisk").gr_gid
directory.mkdir(mode=0o750, parents=True, exist_ok=True)
os.chown(directory, -1, group_id)
directory.chmod(0o750)

with tempfile.TemporaryDirectory(prefix="asterisk-ivr-") as temporary:
    source = Path(temporary) / "source.wav"
    converted = Path(temporary) / "converted.wav"
    for name, text in prompts.items():
        subprocess.run(
            [espeak, "-v", "ru", "-s", "155", "-w", str(source), "--stdin"],
            input=text, encoding="utf-8", check=True,
        )
        subprocess.run(
            [sox, str(source), "-r", "8000", "-c", "1", "-b", "16",
             "-e", "signed-integer", str(converted), "gain", "-n", "-3"],
            check=True,
        )
        destination = directory / f"{name}.wav"
        with converted.open("rb") as incoming, destination.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing)
        os.chown(destination, -1, group_id)
        destination.chmod(0o640)
        print(f"Created: {destination}")
