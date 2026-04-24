#!/usr/bin/env python3

from __future__ import annotations

import argparse
import ctypes
import functools
import http.server
import importlib.util
import json
import os
from pathlib import Path
import select
import struct
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
RELOAD_EVENT_ENDPOINT = "/__events__"

IN_ACCESS = 0x00000001
IN_ATTRIB = 0x00000004
IN_CLOSE_WRITE = 0x00000008
IN_CREATE = 0x00000100
IN_DELETE = 0x00000200
IN_DELETE_SELF = 0x00000400
IN_MODIFY = 0x00000002
IN_MOVE_SELF = 0x00000800
IN_MOVED_FROM = 0x00000040
IN_MOVED_TO = 0x00000080
IN_Q_OVERFLOW = 0x00004000
IN_IGNORED = 0x00008000
IN_EVENT_MASK = (
    IN_ATTRIB
    | IN_CLOSE_WRITE
    | IN_CREATE
    | IN_DELETE
    | IN_DELETE_SELF
    | IN_MODIFY
    | IN_MOVE_SELF
    | IN_MOVED_FROM
    | IN_MOVED_TO
    | IN_Q_OVERFLOW
    | IN_IGNORED
)

LIVE_RELOAD_SNIPPET = """\
<script>
(() => {
  const endpoint = "/__events__";
  let currentBuildVersion = null;
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

  function handlePayload(payload) {
    if (currentBuildVersion === null) {
      currentBuildVersion = payload.version;
    } else if (payload.version !== currentBuildVersion) {
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
  }

  function connect() {
    const events = new EventSource(endpoint);

    events.onmessage = (event) => {
      try {
        handlePayload(JSON.parse(event.data));
      } catch (error) {
        console.error(error);
      }
    };

    events.onerror = () => {
      showBanner("Live reload disconnected.", "error");
    };
  }

  connect();
})();
</script>
"""


class ReloadState:
    def __init__(self) -> None:
        self.event_id = 0
        self.build_version = 0
        self.last_error: str | None = None
        self.condition = threading.Condition()

    def mark_built(self) -> None:
        with self.condition:
            self.event_id += 1
            self.build_version += 1
            self.last_error = None
            self.condition.notify_all()

    def mark_failed(self, error_message: str) -> None:
        with self.condition:
            self.event_id += 1
            self.last_error = error_message
            self.condition.notify_all()

    def snapshot(self) -> tuple[int, int, str | None]:
        with self.condition:
            return self.event_id, self.build_version, self.last_error

    def wait_for_change(self, last_event_id: int, timeout: float) -> tuple[int, int, str | None]:
        with self.condition:
            if self.event_id == last_event_id:
                self.condition.wait(timeout=timeout)
            return self.event_id, self.build_version, self.last_error


class DevRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str | None = None, **kwargs) -> None:
        super().__init__(*args, directory=directory, **kwargs)

    def do_GET(self) -> None:
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.path == RELOAD_ENDPOINT:
            self.serve_reload_status()
            return
        if parsed.path == RELOAD_EVENT_ENDPOINT:
            self.serve_reload_events()
            return
        if self.try_serve_html(parsed.path):
            return
        super().do_GET()

    def log_message(self, format: str, *args) -> None:
        request_path = urllib.parse.urlsplit(self.path).path
        if request_path in (RELOAD_ENDPOINT, RELOAD_EVENT_ENDPOINT):
            return
        super().log_message(format, *args)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def serve_reload_status(self) -> None:
        _, build_version, error_message = self.server.reload_state.snapshot()
        payload = json.dumps(
            {
                "version": build_version,
                "error": error_message,
            }
        ).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def serve_reload_events(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        last_event_id = -1
        while True:
            event_id, build_version, error_message = self.server.reload_state.wait_for_change(
                last_event_id,
                timeout=30.0,
            )

            try:
                if event_id == last_event_id:
                    self.wfile.write(b": keep-alive\n\n")
                else:
                    payload = json.dumps(
                        {
                            "version": build_version,
                            "error": error_message,
                        }
                    )
                    message = f"id: {event_id}\ndata: {payload}\n\n".encode("utf-8")
                    self.wfile.write(message)
                    last_event_id = event_id
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                return

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


def rebuild_after_change(reload_state: ReloadState) -> None:
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


def collect_watch_snapshot() -> dict[str, int]:
    watched_paths = {BUILD_SCRIPT, *STORIES_DIR.glob("*.md")}
    snapshot: dict[str, int] = {}
    for path in watched_paths:
        if path.exists():
            snapshot[str(path)] = path.stat().st_mtime_ns
    return snapshot


def watch_sources_polling(reload_state: ReloadState, interval: float) -> None:
    previous_snapshot = collect_watch_snapshot()
    print(f"[watch] using polling every {interval:g}s")

    while True:
        time.sleep(interval)
        current_snapshot = collect_watch_snapshot()
        if current_snapshot == previous_snapshot:
            continue

        previous_snapshot = current_snapshot
        rebuild_after_change(reload_state)


class InotifySourceWatcher:
    def __init__(self) -> None:
        if not sys.platform.startswith("linux"):
            raise RuntimeError("inotify is only available on Linux")

        self.libc = ctypes.CDLL("libc.so.6", use_errno=True)
        self.fd = self.libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
        if self.fd < 0:
            errno = ctypes.get_errno()
            raise OSError(errno, os.strerror(errno))

        self.watches: dict[int, Path] = {}
        self.add_watch(STORIES_DIR)
        self.add_watch(BUILD_SCRIPT.parent)

    def add_watch(self, path: Path) -> None:
        watch_descriptor = self.libc.inotify_add_watch(
            self.fd,
            os.fsencode(path),
            IN_EVENT_MASK,
        )
        if watch_descriptor < 0:
            errno = ctypes.get_errno()
            raise OSError(errno, os.strerror(errno), str(path))
        self.watches[watch_descriptor] = path

    def close(self) -> None:
        os.close(self.fd)

    def wait_for_source_change(self) -> None:
        while True:
            readable, _, _ = select.select([self.fd], [], [])
            if not readable:
                continue
            if self.read_changed_events():
                return

    def drain_pending_events(self) -> None:
        while True:
            readable, _, _ = select.select([self.fd], [], [], 0)
            if not readable:
                return
            self.read_changed_events()

    def read_changed_events(self) -> bool:
        try:
            data = os.read(self.fd, 65536)
        except BlockingIOError:
            return False

        changed = False
        offset = 0
        header_size = struct.calcsize("iIII")
        while offset + header_size <= len(data):
            watch_descriptor, mask, _, name_length = struct.unpack_from("iIII", data, offset)
            offset += header_size
            raw_name = data[offset : offset + name_length].rstrip(b"\0")
            offset += name_length

            path = self.watches.get(watch_descriptor)
            if path is None:
                continue

            name = os.fsdecode(raw_name) if raw_name else ""
            if path == STORIES_DIR and (not name or name.endswith(".md")):
                changed = True
            elif path == BUILD_SCRIPT.parent and name == BUILD_SCRIPT.name:
                changed = True
            elif mask & IN_Q_OVERFLOW:
                changed = True

        return changed


def watch_sources_events(reload_state: ReloadState, debounce: float) -> None:
    watcher = InotifySourceWatcher()
    print("[watch] using filesystem events")
    try:
        while True:
            watcher.wait_for_source_change()
            time.sleep(debounce)
            watcher.drain_pending_events()
            rebuild_after_change(reload_state)
    finally:
        watcher.close()


def watch_sources(reload_state: ReloadState, watch_mode: str, interval: float, debounce: float) -> None:
    if watch_mode in ("auto", "events"):
        try:
            watch_sources_events(reload_state, debounce)
            return
        except Exception as error:
            if watch_mode == "events":
                raise
            print(f"[watch] filesystem events unavailable; falling back to polling ({error})")

    watch_sources_polling(reload_state, interval)


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
        help="Fallback polling interval in seconds when filesystem events are unavailable.",
    )
    parser.add_argument(
        "--debounce",
        type=float,
        default=0.12,
        help="Seconds to wait after a filesystem event before rebuilding.",
    )
    parser.add_argument(
        "--watch-mode",
        choices=("auto", "events", "poll"),
        default="auto",
        help="Use filesystem events when available, or force polling.",
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
        args=(reload_state, args.watch_mode, args.interval, args.debounce),
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
