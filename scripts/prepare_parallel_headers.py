from pathlib import Path

xml_path = Path("/etc/asterisk/sipp/provider-uac-parallel.xml")
script_path = Path("/usr/local/sbin/test_queue_headers_parallel.sh")
if xml_path.exists() or script_path.exists():
    raise SystemExit("Output already exists; nothing overwritten")

xml = Path("/etc/asterisk/sipp/provider-uac.xml").read_text()
old = "X-Customer-ID: customer-001"
if xml.count(old) != 1:
    raise SystemExit("Unexpected XML content")
xml = xml.replace(old, "X-Customer-ID: customer-[call_number]")
script = Path("/usr/local/sbin/test_queue_headers.sh").read_text()
for old, new in (
    ("lab-headers.log", "lab-headers-parallel.log"),
    ("provider-uac.xml", "provider-uac-parallel.xml"),
    ("-r 1 -m 1", "-r 1 -m 2 -l 2"),
    ("sipp-inbound-74990000000-", "sipp-parallel-74990000000-"),
):
    if old not in script:
        raise SystemExit("Missing expected fragment: " + old)
    script = script.replace(old, new)
with xml_path.open("x") as output:
    output.write(xml)
with script_path.open("x") as output:
    output.write(script)
xml_path.chmod(0o644)
script_path.chmod(0o644)
print("Created:", xml_path, "and", script_path)
