"""The dashboard served end-to-end over real HTTP against the real DB: the exact
requests a judge's browser makes."""

import json
import threading
import urllib.error
import urllib.request
from collections.abc import Iterator
from http.server import ThreadingHTTPServer

import pytest

from cornercheck.app.web import _Handler


@pytest.fixture
def base_url(db: str) -> Iterator[str]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()


def _get(url: str) -> tuple[int, bytes, str]:
    with urllib.request.urlopen(url, timeout=10) as r:
        return r.status, r.read(), r.headers.get("Content-Type", "")


def test_dashboard_page_serves(base_url: str) -> None:
    code, body, ctype = _get(base_url + "/")
    assert code == 200 and "text/html" in ctype
    assert b"refuses" in body and b"provebtn" in body


def test_stats_endpoint_serves_live_numbers(base_url: str) -> None:
    code, body, ctype = _get(base_url + "/api/stats")
    assert code == 200 and "application/json" in ctype
    s = json.loads(body)
    assert s["fighters"] and s["fighters"] > 100  # real DB counts, not hardcoded
    assert s["cases"] >= 54
    assert s["chain"]["ok"] in (True, False, None)


def test_proof_endpoint_proves_over_http(base_url: str) -> None:
    code, body, _ = _get(base_url + "/api/proof")
    p = json.loads(body)
    assert code == 200
    assert p["healthy"] is True and p["proof"] == "PROVEN"


def test_healthz_still_answers(base_url: str) -> None:
    code, body, _ = _get(base_url + "/healthz")
    assert code == 200 and json.loads(body) == {"status": "ok"}


def test_unknown_paths_are_404_not_false_200(base_url: str) -> None:
    try:
        urllib.request.urlopen(base_url + "/favicon.ico", timeout=10)
        raise AssertionError("expected 404")
    except urllib.error.HTTPError as e:
        assert e.code == 404


def test_head_requests_answer_for_uptime_monitors(base_url: str) -> None:
    req = urllib.request.Request(base_url + "/healthz", method="HEAD")
    with urllib.request.urlopen(req, timeout=10) as r:
        assert r.status == 200
        assert r.read() == b""  # headers only


def test_server_header_does_not_fingerprint_python(base_url: str) -> None:
    with urllib.request.urlopen(base_url + "/healthz", timeout=10) as r:
        server = r.headers.get("Server", "")
    assert "Python" not in server and "BaseHTTP" not in server
