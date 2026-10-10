"""Synthetic ClamAV protocol peers only; not real-engine malware acceptance."""
from pathlib import Path
from datetime import datetime, timedelta, timezone
import socket
import struct
import tempfile
import threading
import time
import unittest
from unittest.mock import patch


class ClamdScannerTests(unittest.TestCase):
    def scan_with_peer(self, data, responses, delay=0):
        from app.services.legal_malware import ClamdScanner
        with tempfile.TemporaryDirectory(prefix="legal-scanner-") as directory:
            path = str(Path(directory) / "clamd.sock")
            received = bytearray()
            errors = []
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
                server.bind(path)
                server.listen(1)
                server.settimeout(2)

                def peer():
                    try:
                        with server.accept()[0] as connection:
                            connection.settimeout(2)
                            def exact(size):
                                result = bytearray()
                                while len(result) < size:
                                    chunk = connection.recv(size - len(result))
                                    if not chunk:
                                        raise EOFError("incomplete synthetic stream")
                                    result.extend(chunk)
                                return bytes(result)
                            self.assertEqual(exact(10), b"zINSTREAM\0")
                            while size := struct.unpack("!I", exact(4))[0]:
                                self.assertLessEqual(size, 65536)
                                received.extend(exact(size))
                            time.sleep(delay)
                            for response in responses:
                                connection.sendall(response)
                    except (BrokenPipeError, ConnectionResetError):
                        pass  # expected when the bounded client rejects/ times out
                    except Exception as error:
                        errors.append(error)

                worker = threading.Thread(target=peer)
                worker.start()
                result = ClamdScanner(path, timeout_seconds=0.1 if delay else 2, max_signature_age_hours=None)(data)
                worker.join(3)
                self.assertFalse(worker.is_alive())
                self.assertEqual(errors, [])
                self.assertEqual(bytes(received), data)
                return result

    def test_exact_clean_response_and_chunked_bytes(self):
        self.assertEqual(self.scan_with_peer(b"SYNTHETIC\n" * 10000, [b"stream: ", b"OK\0"]), (True, "clean"))

    def test_detection_is_generic_and_does_not_leak_signature(self):
        self.assertEqual(self.scan_with_peer(b"SYNTHETIC", [b"stream: private-signature FOUND\0"]),
                         (False, "detected"))

    def test_non_clean_incomplete_oversize_or_ambiguous_reply_fails_closed(self):
        for reply in (b"", b"stream: OK", b"OK\0", b"stream: OK\0extra", b"stream: OK\n",
                      b"stream: scan limit ERROR\0", b"x" * 4097, b"stream: OK\0stream: bad FOUND\0"):
            with self.subTest(reply=reply[:40]):
                self.assertEqual(self.scan_with_peer(b"SYNTHETIC", [reply]), (False, "unavailable"))

    def test_timeout_and_missing_socket_fail_closed(self):
        from app.services.legal_malware import ClamdScanner
        self.assertEqual(self.scan_with_peer(b"SYNTHETIC", [b"stream: OK\0"], delay=0.2),
                         (False, "unavailable"))
        self.assertEqual(ClamdScanner("/tmp/legal-synthetic-missing-clamd.sock")(b"SYNTHETIC"),
                         (False, "unavailable"))

    def test_deadline_is_total_not_reset_per_read(self):
        from app.services.legal_malware import ClamdScanner
        with patch("app.services.legal_malware.time.monotonic", side_effect=[0, 0, 0, 0, 31]):
            with patch("app.services.legal_malware.socket.socket") as factory:
                factory.return_value.__enter__.return_value.recv.return_value = b"s"
                self.assertEqual(ClamdScanner("/tmp/synthetic.sock", max_signature_age_hours=None)(b"SYNTHETIC"),
                                 (False, "unavailable"))

    def test_configuration_is_optional_local_absolute_and_bounded(self):
        from app.core.config import Settings
        from app.services.legal_malware import configured_scanner
        settings = Settings(_env_file=None, model_name="qwen3.5:9b")
        self.assertIsNone(configured_scanner(settings))
        for path in ("relative.sock", "http://remote.invalid", "/tmp/a\0b", "//remote/share.sock"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                Settings(_env_file=None, model_name="qwen3.5:9b", legal_clamd_socket=path)
        settings = Settings(_env_file=None, model_name="qwen3.5:9b", legal_clamd_socket="/tmp/synthetic.sock")
        self.assertEqual(configured_scanner(settings).max_signature_age_hours, 72)
        for timeout in (0, -1, 31, float("nan"), float("inf")):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                Settings(_env_file=None, model_name="qwen3.5:9b", legal_scan_timeout_seconds=timeout)
        from app.services.legal_malware import ClamdScanner
        for path in ("", "/" + "s" * 107):
            with self.subTest(path=path), self.assertRaises(ValueError):
                ClamdScanner(path)
        for age in (0, 169, float("nan"), float("inf")):
            with self.subTest(age=age), self.assertRaises(ValueError):
                ClamdScanner("/tmp/synthetic.sock", max_signature_age_hours=age)
            with self.subTest(setting_age=age), self.assertRaises(ValueError):
                Settings(_env_file=None, model_name="qwen3.5:9b", legal_signature_max_age_hours=age)

    def test_configured_scanner_refuses_stale_or_invalid_signature_version_before_bytes(self):
        from app.core.config import Settings
        from app.services.legal_malware import configured_scanner
        now = datetime.now(timezone.utc)
        stale = (now - timedelta(days=4)).strftime("%a %b %d %H:%M:%S %Y")
        future = (now + timedelta(days=1)).strftime("%a %b %d %H:%M:%S %Y")
        for reply in (b"", b"ClamAV invalid\0", f"ClamAV 1.5.4/28147/{stale}\0".encode(),
                      f"ClamAV 1.5.4/28147/{future}\0".encode(), b"x" * 4097):
            with self.subTest(reply=reply[:40]):
                with patch("app.services.legal_malware.socket.socket") as factory:
                    connection = factory.return_value.__enter__.return_value
                    connection.recv.side_effect = [reply, b""]
                    result = configured_scanner(Settings(_env_file=None, model_name="qwen3.5:9b",
                        legal_clamd_socket="/tmp/synthetic.sock"))(b"SYNTHETIC must not be streamed")
                    self.assertEqual(result, (False, "unavailable"))
                    self.assertEqual(connection.sendall.call_args_list[0].args, (b"zVERSION\0",))
                    self.assertEqual(connection.sendall.call_count, 1)

    def test_configured_scanner_checks_fresh_signatures_then_streams(self):
        from app.core.config import Settings
        from app.services.legal_malware import configured_scanner
        timestamp = datetime.now(timezone.utc).strftime("%a %b %d %H:%M:%S %Y")
        version = f"ClamAV 1.5.4/28147/{timestamp}\0".encode()
        with patch("app.services.legal_malware.socket.socket") as factory:
            connection = factory.return_value.__enter__.return_value
            connection.recv.side_effect = [version, b"", b"stream: OK\0", b""]
            result = configured_scanner(Settings(_env_file=None, model_name="qwen3.5:9b",
                legal_clamd_socket="/tmp/synthetic.sock"))(b"SYNTHETIC current signatures")
            self.assertEqual(result, (True, "clean"))
            self.assertEqual(connection.sendall.call_args_list[0].args, (b"zVERSION\0",))
            self.assertEqual(factory.call_count, 2)

    def test_signature_preflight_and_scan_share_one_deadline(self):
        from app.core.config import Settings
        from app.services.legal_malware import configured_scanner
        timestamp = datetime.now(timezone.utc).strftime("%a %b %d %H:%M:%S %Y")
        with patch("app.services.legal_malware.socket.socket") as factory:
            connection = factory.return_value.__enter__.return_value
            connection.recv.side_effect = [f"ClamAV 1.5.4/28147/{timestamp}\0".encode(), b""]
            with patch("app.services.legal_malware.time.monotonic", side_effect=[0, 0, 0, 0, 0, 31]):
                result = configured_scanner(Settings(_env_file=None, model_name="qwen3.5:9b",
                    legal_clamd_socket="/tmp/synthetic.sock"))(b"SYNTHETIC timeout must not stream")
            self.assertEqual(result, (False, "unavailable"))
            self.assertEqual(connection.sendall.call_args_list[0].args, (b"zVERSION\0",))
            self.assertEqual(connection.sendall.call_count, 1)


if __name__ == "__main__":
    unittest.main()
