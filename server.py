"""
server.py — Chhota HTTP API taaki n8n (ya koi bhi tool) pipeline ko trigger kar sake.

Koi extra install nahi (Python stdlib). n8n orchestration karta hai (schedule + notify +
upload), heavy Python yahan chalta hai. n8n local ho ya Docker — dono se kaam karega.

Chalao:
    env\\Scripts\\python.exe server.py            # http://localhost:8000

Endpoints:
    GET  /health                      -> {"ok": true}
    POST /build   {"n":1,"topic":""}  -> ek/kai shorts banata hai, summary deta hai
                                         (SYNC: build poora hone tak wait karta hai)
    GET  /latest                      -> pichhle build ka summary (output/auto/done.json)
    POST /upload  {"dir":"output/auto/.../01_...","privacy":"unlisted"}
                                      -> us video ko YouTube pe upload (token.json chahiye)

NOTE: build ~5-6 min/video (CPU). n8n HTTP Request node ka timeout BADA rakho (e.g. 1200000ms),
ya /build ke baad thodी der ruk ke /latest padho.
"""

import os
import sys
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

PORT = int(os.getenv("PORT", "8000"))
_BUILD_LOCK = threading.Lock()   # ek time pe ek hi build (CPU heavy)


def _json_body(handler):
    try:
        n = int(handler.headers.get("Content-Length", 0))
        raw = handler.rfile.read(n) if n else b"{}"
        return json.loads(raw or b"{}")
    except Exception:
        return {}


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        print("[server]", *a)

    def do_GET(self):
        if self.path == "/health":
            return self._send(200, {"ok": True})
        if self.path == "/latest":
            p = os.path.join("output", "auto", "done.json")
            if os.path.exists(p):
                with open(p, encoding="utf-8") as f:
                    return self._send(200, json.load(f))
            return self._send(404, {"error": "no build yet"})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        body = _json_body(self)
        if self.path == "/build":
            if not _BUILD_LOCK.acquire(blocking=False):
                return self._send(409, {"error": "build already running"})
            try:
                n = int(body.get("n", 1))
                topic = (body.get("topic") or "").strip() or None
                print(f"[server] /build n={n} topic={topic!r}")
                import auto
                summary = auto.autopilot(n, topic)
                return self._send(200, summary)
            except Exception as e:
                import traceback
                traceback.print_exc()
                return self._send(500, {"error": str(e)})
            finally:
                _BUILD_LOCK.release()

        if self.path == "/upload":
            d = (body.get("dir") or "").strip()
            privacy = (body.get("privacy") or "unlisted").strip()
            if not d or not os.path.isdir(d):
                return self._send(400, {"error": "valid 'dir' chahiye"})
            try:
                import upload_youtube
                if not upload_youtube.is_authed():
                    return self._send(400, {"error": "YouTube auth nahi (token.json). "
                                            "Pehle: python upload_youtube.py auth"})
                url = upload_youtube.upload_from_output(privacy, outdir=d)
                return self._send(200, {"url": url, "privacy": privacy})
            except Exception as e:
                import traceback
                traceback.print_exc()
                return self._send(500, {"error": str(e)})

        return self._send(404, {"error": "not found"})


class DualStackServer(ThreadingHTTPServer):
    """localhost (IPv6 ::1) AUR 127.0.0.1 (IPv4) dono pe sunta hai — taaki
    Node/n8n ka 'localhost' (jo IPv6 try karta hai) bhi connect ho jaye."""
    address_family = socket.AF_INET6

    def server_bind(self):
        try:
            self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        except (AttributeError, OSError):
            pass
        super().server_bind()


if __name__ == "__main__":
    print(f"🚀 Football-shorts API -> http://localhost:{PORT}  (IPv4 + IPv6)")
    print("   POST /build {\"n\":1}   |   GET /latest   |   POST /upload {\"dir\":..}")
    try:
        DualStackServer(("::", PORT), Handler).serve_forever()
    except OSError:
        # IPv6 na chale to plain IPv4 fallback
        ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
