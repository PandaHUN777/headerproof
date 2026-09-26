from __future__ import annotations

import socket
import struct
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib import request

from headerproof.detectors import analyze_oob_header_probe
from headerproof.models import HttpSnapshot
from headerproof.oob import OOBEventStore, _http_handler, make_dns_server, query_events


def snapshot() -> HttpSnapshot:
    return HttpSnapshot(
        request_method="GET",
        request_url="https://example.com/",
        status=200,
        reason="OK",
        headers={"content-type": ["text/html"]},
        body_sample="",
        elapsed_ms=1,
        request_headers={"X-Forwarded-Host": "token.oob.local"},
        client_context="oob-test",
    )


def test_http_callback_and_event_query(tmp_path: Path) -> None:
    store = OOBEventStore(tmp_path / "events.jsonl")
    server = ThreadingHTTPServer(("127.0.0.1", 0), _http_handler(store))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        with request.urlopen(f"{base}/c/abc123", timeout=1) as response:
            assert response.status == 200
        events = query_events(base, "abc123")
        assert len(events) == 1
        assert events[0]["protocol"] == "http"
        assert (tmp_path / "events.jsonl").exists()
    finally:
        server.shutdown()
        server.server_close()


def _dns_query(name: str) -> bytes:
    labels = b"".join(bytes([len(part)]) + part.encode("ascii") for part in name.split(".")) + b"\x00"
    return struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0) + labels + struct.pack("!HH", 1, 1)


def test_dns_callback_records_token() -> None:
    store = OOBEventStore()
    server = make_dns_server("127.0.0.1", 0, store, "oob.local", "127.0.0.1")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.sendto(_dns_query("deadbeef.oob.local"), server.server_address)
        response, _ = sock.recvfrom(512)
        assert response[:2] == b"\x12\x34"
        assert store.events("deadbeef")[0]["protocol"] == "dns"
    finally:
        server.shutdown()
        server.server_close()


def test_oob_signal_passes_template_gate() -> None:
    signals = analyze_oob_header_probe(
        "X-Forwarded-Host",
        "deadbeef",
        [{"protocol": "dns"}, {"protocol": "http"}],
        snapshot(),
        False,
    )

    assert len(signals) == 1
    assert signals[0]["type"] == "blind_header_oob_confirmed"
    assert signals[0]["assessment"]["technical_gate"] == "passed"
    assert signals[0]["assessment"]["state"] == "cross_request_confirmed"
