#!/usr/bin/env python3
"""Inspect PJSIP contacts; --write publishes registered TP phones to AstDB."""
import argparse
import configparser
import re
import socket
import sys
import time
from pathlib import Path


class AMI:
    def __init__(self, connection, reader):
        self.connection = connection
        self.reader = reader
        self.serial = 0

    def message(self, deadline):
        result = {}
        size = 0
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("AMI action timed out")
            self.connection.settimeout(min(5, remaining))
            line = self.reader.readline(8193)
            if not line:
                raise ConnectionError("AMI disconnected")
            size += len(line)
            if len(line) > 8192 or size > 65536:
                raise ValueError("AMI message too large")
            if line in (b"\r\n", b"\n"):
                if result:
                    return result
                continue
            key, separator, value = line.decode("utf-8", errors="replace").partition(":")
            if not separator:
                raise ValueError("Invalid AMI message")
            result[key.lower()] = value.strip()

    def action(self, name, complete=None, **fields):
        self.serial += 1
        action_id = str(self.serial)
        headers = {"Action": name, "ActionID": action_id, **fields}
        for key, value in headers.items():
            if any(c in str(key) + str(value) for c in "\r\n"):
                raise ValueError("Invalid AMI header")
        payload = "".join(f"{key}: {value}\r\n" for key, value in headers.items())
        self.connection.sendall((payload + "\r\n").encode("utf-8"))
        deadline = time.monotonic() + 15
        events = []
        acknowledged = False
        while True:
            message = self.message(deadline)
            if message.get("actionid") != action_id:
                continue
            if message.get("response") == "Error":
                raise RuntimeError(f"AMI action rejected: {name}")
            if message.get("response") == "Success":
                acknowledged = True
                if complete is None:
                    return message
            if complete and message.get("event") == complete:
                if not acknowledged or int(message.get("listitems", "-1")) != len(events):
                    raise ValueError("Incomplete AMI contact list")
                return events
            if message.get("event") == "ContactList":
                events.append(message)
                if len(events) > 10000:
                    raise ValueError("Too many AMI contacts")


def registered_tp(contacts, now):
    numbers = set()
    for contact in contacts:
        number = contact.get("endpoint", "")
        if not re.fullmatch(r"34[0-9]{2}", number):
            continue
        # Dynamic registrations expire; static contacts have expiration zero.
        expires = int(contact["expirationtime"])
        if expires > now:
            numbers.add(number)
    return sorted(numbers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Update tp/snapshot in AstDB")
    args = parser.parse_args()
    config = configparser.ConfigParser(interpolation=None)
    with Path("/etc/asterisk/local/manager-tp.conf").open(encoding="utf-8") as source:
        config.read_file(source)
    secret = config["tp-sync"]["secret"]
    with socket.create_connection(("127.0.0.1", 5038), timeout=5) as connection:
        with connection.makefile("rb") as reader:
            if not reader.readline(256).startswith(b"Asterisk Call Manager/"):
                raise ValueError("Unexpected AMI greeting")
            ami = AMI(connection, reader)
            ami.action("Login", Username="tp-sync", Secret=secret, Events="off")
            observed_at = int(time.time())
            contacts = ami.action("PJSIPShowContacts", complete="ContactListComplete")
            if not args.write:
                for contact in contacts:
                    number = contact.get("endpoint", "")
                    if re.fullmatch(r"34[0-9]{2}", number):
                        print(f"Endpoint={number} Status={contact.get('status', '?')} "
                              f"ExpirationTime={contact.get('expirationtime', '?')}")
                print(f"Read {len(contacts)} contacts; AstDB unchanged")
                return
            numbers = registered_tp(contacts, int(time.time()))
            snapshot = f"{observed_at}|{','.join(numbers)}"
            ami.action("DBPut", Family="tp", Key="snapshot", Val=snapshot)
            print(f"Updated tp/snapshot: {snapshot} (count={len(numbers)})")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, configparser.Error, RuntimeError) as error:
        # Never print the parsed credential file or the Login request.
        print(f"TP sync failed: {type(error).__name__}", file=sys.stderr)
        sys.exit(1)
