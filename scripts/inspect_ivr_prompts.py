#!/usr/bin/env python3
"""Display actual WAV format and duration for the three IVR prompts."""
import wave
from pathlib import Path

directory = Path("/var/lib/asterisk/sounds/custom")
for name in ("ivr-welcome", "ivr-invalid", "ivr-unavailable"):
    with wave.open(str(directory / f"{name}.wav"), "rb") as audio:
        print(
            name,
            "channels=", audio.getnchannels(),
            "rate=", audio.getframerate(),
            "bits=", audio.getsampwidth() * 8,
            "compression=", audio.getcomptype(),
            "seconds=", round(audio.getnframes() / audio.getframerate(), 2),
        )
