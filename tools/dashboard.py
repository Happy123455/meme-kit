"""Meme review dashboard: serves the kit locally and saves your ratings into meta/ratings.json.
  python3 tools/dashboard.py            → opens http://localhost:8765/tools/dashboard/
  python3 tools/dashboard.py --camfx    → opens the Camera FX page (tools/dashboard/camfx.html)
Per item (meta/ratings.json, key "type:id"): rating favorite/good/meh/never, note, trim [a, b] seconds, mute (clip audio off),
pair {sound, at, note} (use this library sound with the clip), screen "full"/"window" (always / never full screen). After reviewing, run tools/rebuild_catalog.py
(the dashboard's "Save to catalog" button does it for you) so sessions prefer favourites and skip "never"."""
import json, os, re, subprocess, sys, threading, webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

KIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(KIT)
RATINGS = "meta/ratings.json"; PORT = int(os.environ.get("PORT", 8765)); LOCK = threading.Lock()


def load():
    return json.load(open(RATINGS)) if os.path.exists(RATINGS) else {}


class H(SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

    def _json(self, obj, code=200):
        b = json.dumps(obj).encode(); self.send_response(code)
        self.send_header("Content-Type", "application/json"); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/api/ratings"): return self._json(load())
        rng = self.headers.get("Range")
        path = self.translate_path(self.path)
        if rng and os.path.isfile(path):  # byte ranges so videos/audio seek (Safari needs this)
            m = re.match(r"bytes=(\d*)-(\d*)", rng); size = os.path.getsize(path)
            a = int(m.group(1)) if m.group(1) else 0; b = int(m.group(2)) if m.group(2) else size - 1; b = min(b, size - 1)
            self.send_response(206); self.send_header("Content-Type", self.guess_type(path)); self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Range", f"bytes {a}-{b}/{size}"); self.send_header("Content-Length", str(b - a + 1)); self.end_headers()
            with open(path, "rb") as f:
                f.seek(a); left = b - a + 1
                while left > 0:
                    chunk = f.read(min(1 << 16, left))
                    if not chunk: break
                    try: self.wfile.write(chunk)
                    except (BrokenPipeError, ConnectionResetError): return
                    left -= len(chunk)
            return
        return super().do_GET()

    def end_headers(self):
        self.send_header("Accept-Ranges", "bytes"); self.send_header("Cache-Control", "no-store"); super().end_headers()

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        if self.path == "/api/rate":  # {key: "type:id", rating?, note?, trim?: [a, b], mute?: bool, pair?: {sound, at, note}, screen?: "full"|"window"}
            with LOCK:
                r = load(); k = body["key"]; cur = r.get(k, {})
                for f in ("rating", "note", "trim", "mute", "pair", "screen"):
                    if f not in body: continue
                    v = body[f]
                    if v in (None, "", False, []): cur.pop(f, None)
                    else: cur[f] = v
                if cur: r[k] = cur
                else: r.pop(k, None)
                json.dump(r, open(RATINGS, "w"), indent=1, sort_keys=True, ensure_ascii=False)
            return self._json(dict(ok=True, count=len(r)))
        if self.path == "/api/rebuild":
            out = subprocess.run([sys.executable, "tools/rebuild_catalog.py"], capture_output=True, text=True)
            return self._json(dict(ok=out.returncode == 0, log=(out.stdout + out.stderr)[-400:]))
        self._json(dict(error="unknown"), 404)


if __name__ == "__main__":
    url = f"http://localhost:{PORT}/tools/dashboard/" + ("camfx.html" if "--camfx" in sys.argv else "")
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    except OSError:  # already running (e.g. double-clicked twice) → just open the page
        print("Dashboard is already running:", url); webbrowser.open(url); sys.exit(0)
    print("Meme dashboard:", url, "(Ctrl+C to stop)")
    if "--no-open" not in sys.argv: threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try: srv.serve_forever()
    except KeyboardInterrupt: pass
