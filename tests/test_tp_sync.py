"""Protocol replay and registration filtering; no live Asterisk required."""
import io
from pathlib import Path
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sync_tp_contacts import AMI, registered_tp


class FakeConnection:
    def __init__(self):
        self.sent = []

    def settimeout(self, value):
        pass

    def sendall(self, payload):
        self.sent.append(payload)


class SyncTests(unittest.TestCase):
    def test_registration_filter_and_deduplication(self):
        contacts = [
            {"endpoint": "3400", "expirationtime": "110", "status": "Unreachable"},
            {"endpoint": "3400", "expirationtime": "120"},
            {"endpoint": "3499", "expirationtime": "130"},
            {"endpoint": "3401", "expirationtime": "100"},
            {"endpoint": "3402", "expirationtime": "0"},
            {"endpoint": "3300", "expirationtime": "200"},
            {"endpoint": "3500", "expirationtime": "200"},
        ]
        self.assertEqual(registered_tp(contacts, 100), ["3400", "3499"])

    def test_malformed_expiration_rejected(self):
        with self.assertRaises(ValueError):
            registered_tp([{"endpoint": "3400", "expirationtime": "broken"}], 100)

    def test_full_list_and_unrelated_event(self):
        replay = (
            b"Event: SomethingElse\r\nActionID: other\r\n\r\n"
            b"Response: Success\r\nActionID: 1\r\n\r\n"
            b"Event: ContactList\r\nActionID: 1\r\nEndpoint: 3400\r\n\r\n"
            b"Event: ContactListComplete\r\nActionID: 1\r\nListItems: 1\r\n\r\n"
        )
        connection = FakeConnection()
        contacts = AMI(connection, io.BytesIO(replay)).action(
            "PJSIPShowContacts", complete="ContactListComplete")
        self.assertEqual(contacts, [{"event": "ContactList", "actionid": "1", "endpoint": "3400"}])
        self.assertIn(b"Action: PJSIPShowContacts\r\n", connection.sent[0])

    def test_incomplete_list_rejected(self):
        replay = (
            b"Response: Success\r\nActionID: 1\r\n\r\n"
            b"Event: ContactListComplete\r\nActionID: 1\r\nListItems: 1\r\n\r\n"
        )
        with self.assertRaises(ValueError):
            AMI(FakeConnection(), io.BytesIO(replay)).action(
                "PJSIPShowContacts", complete="ContactListComplete")

    def test_action_error_rejected(self):
        with self.assertRaises(RuntimeError):
            AMI(FakeConnection(), io.BytesIO(
                b"Response: Error\r\nActionID: 1\r\n\r\n")).action("DBPut")

    def test_disconnect_rejected(self):
        with self.assertRaises(ConnectionError):
            AMI(FakeConnection(), io.BytesIO(b"")).action("Login")

    def test_header_injection_rejected(self):
        connection = FakeConnection()
        with self.assertRaises(ValueError):
            AMI(connection, io.BytesIO(b"")).action("Login", Secret="x\r\nAction: DBPut")
        self.assertEqual(connection.sent, [])


if __name__ == "__main__":
    unittest.main()
