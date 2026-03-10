#!/usr/bin/env python3

from __future__ import annotations

import argparse
import functools
import http.server
import importlib.util
import json
from pathlib import Path
import sys
import threading
import time
import traceback
import urllib.parse


ROOT = Path(__file__).resolve().parent.parent
SITE_DIR = ROOT / "site"
STORIES_DIR = ROOT / "stories"
BUILD_SCRIPT = Path(__file__).resolve().parent / "build_site.py"
RELOAD_ENDPOINT = "/__reload__"

LIVE_RELOAD_SNIPPET = """\
<script>
(() => {
  const endpoint = "/__reload__";
  let currentVersion = null;
  let lastError = null;
  let banner = null;

  function ensureBanner() {
    if (banner) return banner;
    banner = document.createElement("div");
    banner.style.cssText = [
      "position:fixed",
      "right:16px",
      "bottom:16px",
      "z-index:9999",
      "padding:10px 14px",
      "border-radius:999px",
      "font:12px/1.2 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
      "box-shadow:0 8px 24px rgba(0,0,0,0.16)"
    ].join(";");
    document.body.appendChild(banner);
    return banner;
  }

  function showBanner(message, kind) {
    const node = ensureBanner();
    node.textContent = message;
    if (kind === "error") {
      node.style.background = "rgba(132, 26, 26, 0.95)";
      node.style.color = "#fff7f7";
    } else {
      node.style.background = "rgba(20, 84, 72, 0.92)";
      node.style.color = "#f7fffc";
    }
  }

  function hideBanner() {
    if (!banner) return;
    banner.remove();
    banner = null;
  }

  async function poll() {
    try {
      const response = await fetch(endpoint, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const payload = await response.json();

      if (currentVersion === null) {
        currentVersion = payload.version;
      } else if (payload.version !== currentVersion) {
        window.location.reload();
        return;
      }

      if (payload.error) {
        if (payload.error !== lastError) {
          console.error(payload.error);
        }
        lastError = payload.error;
        showBanner("Build failed. See terminal.", "error");
      } else {
        lastError = null;
        hideBanner();
      }
    } catch (error) {
      showBanner("Live reload disconnected.", "error");
    } finally {
      window.setTimeout(poll, 1000);
    }
  }

  poll();
})();
</script>
"""


class ReloadState:
    def __init__(self) -> None:
        self.version = 0
        self.last_error: str | None = None
        self.lock = threading.Lock()

    def mark_built(self) -> None:
        with self.lock:
            self.version += 1
            self.last_error = None

    def mark_failed(self, error_message: str) -> None:
        with self.lock:
            self.last_error = error_message

    def snapshot(self) -> tuple[int, str | None]:
        with self.lock:
            return self.version, self.last_error


class DevRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, **kwargs) -> None:
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == RELOAD_ENDPOINT:
            self.serve_reload_status()
            return
        if self.try_serve_html(parsed.path):
            return
        super().do_GET()

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def serve_reload_status(self) -> None:
        version, error_message = self.server.reload_state.snapshot()
        payload = json.dumps(
            {
                "version": version,
                "error": error_message,
            }
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def try_serve_html(self, request_path: str) -> bool:
        file_path = Path(self.translate_path(request_path))
        if file_path.is_dir():
            file_path = file_path / "index.html"

        if not file_path.is_file() or file_path.suffix.lower() != ".html":
            return False

        html = file_path.read_text(encoding="utf-8")
        if "</body>" in html:
            html = html.replace("</body>", LIVE_RELOAD_SNIPPET + "\n  </body>", 1)
        else:
            html += LIVE_RELOAD_SNIPPET

        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
        return True


class DevServer(http.server.ThreadingHTTPServer):
    def __init__(self, server_address: tuple[str, int], handler_class, reload_state: ReloadState) -> None:
        super().__init__(server_address, handler_class)
        self.reload_state = reload_state


def load_build_module():
    module_name = "mini_novels_build_site"
    spec = importlib.util.spec_from_file_location(module_name, BUILD_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {BUILD_SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def run_build() -> None:
    module = load_build_module()
    module.build_site()


def collect_watch_snapshot() -> dict[str, int]:
    watched_paths = {BUILD_SCRIPT, *STORIES_DIR.glob("*.md")}
    snapshot: dict[str, int] = {}
    for path in watched_paths:
        if path.exists():
            snapshot[str(path)] = path.stat().st_mtime_ns
    return snapshot


def watch_sources(reload_state: ReloadState, interval: float) -> None:
    previous_snapshot = collect_watch_snapshot()

    while True:
        time.sleep(interval)
        current_snapshot = collect_watch_snapshot()
        if current_snapshot == previous_snapshot:
            continue

        previous_snapshot = current_snapshot
        try:
            run_build()
        except Exception:
            error_message = traceback.format_exc()
            reload_state.mark_failed(error_message)
            print("[watch] build failed")
            print(error_message)
        else:
            reload_state.mark_built()
            timestamp = time.strftime("%H:%M:%S")
            print(f"[watch] rebuilt at {timestamp}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Serve `site/` with auto rebuild and browser reload."
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to.")
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Polling interval in seconds for source changes.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    reload_state = ReloadState()

    try:
        run_build()
    except Exception:
        print("[watch] initial build failed")
        print(traceback.format_exc())
        raise SystemExit(1)

    reload_state.mark_built()

    watcher = threading.Thread(
        target=watch_sources,
        args=(reload_state, args.interval),
        daemon=True,
    )
    watcher.start()

    handler = functools.partial(DevRequestHandler, directory=str(SITE_DIR))
    server = DevServer((args.host, args.port), handler, reload_state)

    print(f"[serve] http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[serve] stopped")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
