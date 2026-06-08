"""Health + landing HTTP server.

A Socket Mode Slack app has no inbound HTTP, but a Render web service must bind $PORT.
This tiny stdlib server satisfies that AND gives judges a public URL that shows the
service is live with live audit-chain integrity. Real interaction happens in Slack.
"""

import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

log = logging.getLogger("cornercheck.web")

_LANDING = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CornerCheck</title>
<style>
 :root {{ color-scheme: dark; }}
 * {{ box-sizing: border-box; }}
 body {{ margin:0; font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
   background:#0b1220; color:#e6edf3; }}
 .wrap {{ max-width:720px; margin:0 auto; padding:64px 24px; }}
 h1 {{ font-size:2.2rem; margin:0 0 4px; }}
 .tag {{ color:#9fb3c8; margin:0 0 28px; }}
 .badge {{ display:inline-block; padding:4px 12px; border-radius:999px; font-size:.85rem;
   font-weight:600; }}
 .live {{ background:#10391f; color:#3fb950; }}
 .warn {{ background:#3a2a10; color:#f0a020; }}
 .card {{ background:#111a2b; border:1px solid #1d2a44; border-radius:14px; padding:22px;
   margin:18px 0; }}
 .card h2 {{ margin:0 0 10px; font-size:1.05rem; color:#9fb3c8; text-transform:uppercase;
   letter-spacing:.05em; }}
 code {{ background:#0b1220; padding:2px 6px; border-radius:6px; color:#7ee2b8; }}
 a {{ color:#58a6ff; }}
 .muted {{ color:#7d8aa0; font-size:.9rem; }}
</style></head>
<body><div class="wrap">
 <h1>CornerCheck</h1>
 <p class="tag">Fighter-safety clearance for fight-operations teams.</p>
 <span class="badge {badge_class}">{badge_text}</span>
 <div class="card">
  <h2>What it does</h2>
  Catches cross-jurisdiction medical suspensions, enforces return-to-competition windows,
  surfaces injury chatter from your team's own Slack, and <b>refuses to clear when it can't
  be sure who the fighter is</b>. Decision support: a human always makes the final call, and
  every decision lands in a tamper-evident, hash-chained audit ledger.
 </div>
 <div class="card">
  <h2>Audit chain integrity</h2>
  {chain_line}
 </div>
 <div class="card">
  <h2>How to use it</h2>
  CornerCheck runs as a Slack agent. In the workspace, open the CornerCheck app and ask
  <code>Is &lt;fighter&gt; cleared in &lt;state&gt;?</code>
 </div>
 <p class="muted">Slack Agent Builder Challenge - Agent for Good.
  <a href="https://github.com/StephenSook/cornercheck">Source on GitHub</a>.</p>
</div></body></html>
"""


def _chain_status() -> dict[str, Any]:
    """Best-effort: never let a DB hiccup take down the landing page."""
    try:
        from cornercheck.ledger.verify import verify_chain

        r = verify_chain()
        return {"ok": r.ok, "checked": r.checked, "detail": r.detail}
    except Exception as exc:
        return {"ok": None, "detail": f"chain status unavailable: {exc}"}


def _render_landing() -> bytes:
    status = _chain_status()
    if status["ok"] is True:
        badge_class, badge_text = "live", "● LIVE"
        chain_line = f":lock: intact - {status['checked']} entries verified".replace(
            ":lock:", "&#128274;"
        )
    elif status["ok"] is False:
        badge_class, badge_text = "warn", "● LIVE (chain alert)"
        chain_line = f"&#128680; {status['detail']}"
    else:
        badge_class, badge_text = "live", "● LIVE"
        chain_line = status["detail"]
    return _LANDING.format(
        badge_class=badge_class, badge_text=badge_text, chain_line=chain_line
    ).encode()


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/healthz":
            self._send(200, "application/json", json.dumps({"status": "ok"}).encode())
        else:
            self._send(200, "text/html; charset=utf-8", _render_landing())

    def _send(self, code: int, content_type: str, body: bytes) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: Any) -> None:
        pass  # keep the worker logs clean


def start_health_server(port: int) -> None:
    server = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    threading.Thread(target=server.serve_forever, name="health-server", daemon=True).start()
    log.info("health/landing server bound on 0.0.0.0:%d", port)
