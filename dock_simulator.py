"""
Dock simulator for the dock projects.

It pretends to be a charging dock on your own computer. It replays a real
recording (CSV) and answers the same web addresses as the real dock:

    http://localhost:8080/api/status   -> the dock's state right now (JSON)
    http://localhost:8080/api/events   -> the dock's recent messages (JSON)

Only Python 3 is needed (no extra packages).

Examples:
    python dock_simulator.py data/recording_B_evening.csv
    python dock_simulator.py data/recording_B_evening.csv --speed 10
    python dock_simulator.py data/recording_A_morning.csv --drops 0.05 --restart-every 5

Options:
    --speed N          play N times faster (default 1 = real time)
    --port P           web port (default 8080)
    --drops X          fraction of requests that fail, to test your error handling
                       (for example 0.05 = 5 % of requests time out or return an error)
    --restart-every M  pretend the dock restarts every M minutes (10 s offline, uptime resets)

Press Ctrl+C to stop.
"""
import argparse
import csv
import json
import random
import threading
import time
from bisect import bisect_right
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def load_recording(path):
    """Read the CSV recording into a list of (seconds_from_start, row dict)."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            h, m, s = r["time"].split(":")
            t = int(h) * 3600 + int(m) * 60 + float(s)
            rows.append((t, r))
    if not rows:
        raise SystemExit("The recording is empty: " + path)
    t0 = rows[0][0]
    return [(t - t0, r) for t, r in rows]


class Dock:
    """Replays the recording and keeps a list of events, like the real dock."""

    def __init__(self, rows, speed, restart_every_min):
        self.rows = rows
        self.times = [t for t, _ in rows]
        self.length = self.times[-1] + 1.0
        self.speed = speed
        self.restart_every = restart_every_min * 60 if restart_every_min else 0
        self.started = time.time()
        self.boot_time = time.time()
        self.boot_count = 1
        self.offline_until = 0.0
        self.events = []
        self.total_events = 0
        self.last = None
        self.lock = threading.Lock()
        self._event("Boot (simulator), reset: power-on")

    def _ms(self):
        return int((time.time() - self.boot_time) * 1000)

    def _event(self, text):
        self.total_events += 1
        self.events.append({"ms": self._ms(), "text": text})
        self.events = self.events[-64:]

    def _row_now(self):
        played = ((time.time() - self.started) * self.speed) % self.length
        i = max(0, bisect_right(self.times, played) - 1)
        return self.rows[i][1]

    def tick(self):
        """Advance the simulation; create events when something changes."""
        with self.lock:
            now = time.time()
            if self.restart_every and now - self.boot_time >= self.restart_every:
                self.offline_until = now + 10
                self.boot_time = now + 10
                self.boot_count += 1
                self.events = []
                self.last = None
                self._event("Boot (simulator), reset: power-on")
            if now < self.offline_until:
                return
            r = self._row_now()
            cur = (r["state"], r["relay"] == "True", float(r["pad_v"]))
            if self.last is not None:
                if cur[0] != self.last[0]:
                    self._event("%s -> %s  (%.2f V)" % (self.last[0], cur[0], cur[2]))
                if cur[1] != self.last[1]:
                    self._event("Relay %s" % ("CLOSED" if cur[1] else "OPENED"))
            self.last = cur

    def offline(self):
        return time.time() < self.offline_until

    def status(self):
        with self.lock:
            r = self._row_now()
            return {
                "dock_name": "SIM-DOCK",
                "fw": "simulator-1.0",
                "state": r["state"],
                "pad_v": round(float(r["pad_v"]), 3),
                "relay_closed": r["relay"] == "True",
                "robot_present": r["robot_present"] == "True",
                "fault": r.get("fault", "") or "",
                "uptime_ms": self._ms(),
                "boot_count": self.boot_count,
                "time_unix": int(time.time()),
            }

    def event_list(self):
        with self.lock:
            return {"now_ms": self._ms(), "time_unix": int(time.time()),
                    "total": self.total_events, "events": list(self.events)}


def make_handler(dock, drops):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, obj):
            body = json.dumps(obj).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if dock.offline():
                time.sleep(3)          # like a dock that is restarting: no answer
                self.close_connection = True
                return
            if drops and random.random() < drops:
                if random.random() < 0.5:
                    time.sleep(5)      # looks like a Wi-Fi timeout
                    self.close_connection = True
                    return
                self._send(503, {"error": "simulated network problem"})
                return
            if self.path.startswith("/api/status"):
                self._send(200, dock.status())
            elif self.path.startswith("/api/events"):
                self._send(200, dock.event_list())
            else:
                self._send(404, {"error": "use /api/status or /api/events"})

        def do_POST(self):
            self._send(405, {"error": "the dock is read-only"})

        do_PUT = do_DELETE = do_POST

        def log_message(self, *args):
            pass                       # keep the console quiet

    return Handler


def main():
    ap = argparse.ArgumentParser(description="Replay a dock recording as a fake dock web server.")
    ap.add_argument("recording", help="CSV recording, for example data/recording_B_evening.csv")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--drops", type=float, default=0.0)
    ap.add_argument("--restart-every", type=float, default=0.0)
    a = ap.parse_args()

    dock = Dock(load_recording(a.recording), a.speed, a.restart_every)

    def loop():
        while True:
            dock.tick()
            time.sleep(0.05)
    threading.Thread(target=loop, daemon=True).start()

    server = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(dock, a.drops))
    print("Dock simulator running: http://localhost:%d/api/status" % a.port)
    print("Recording: %s  (%.0f s, plays %.0fx speed, then repeats)" % (a.recording, dock.length, a.speed))
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
