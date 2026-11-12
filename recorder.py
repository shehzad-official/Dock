"""
Dock Recorder: reads the dock status every second and saves it to a CSV file.
It also saves the dock's recent messages (/api/events) to a second CSV file.

Examples:
    python recorder.py
    python recorder.py --out results/A_morning.csv
    python recorder.py --port 8081 --out results/dock2.csv

Press Ctrl+C to stop.
"""
import argparse
import csv
import os
import time
from datetime import datetime, timedelta

import requests

COLUMNS = ["time", "state", "pad_v", "relay_closed", "robot_present", "fault", "uptime_ms", "boot_count", "note"]
EVENT_COLUMNS = ["time", "dock_ms", "text"]


def read_status(url, timeout=2.0, must_have="state"):
    """Ask the dock for one JSON answer.

    Returns (data, None) when it worked,
    or (None, "reason") when it did not.
    """
    try:
        response = requests.get(url, timeout=timeout)
    except requests.exceptions.Timeout:
        return None, "timeout"
    except requests.exceptions.RequestException:
        return None, "no connection"

    if response.status_code != 200:
        return None, "HTTP " + str(response.status_code)

    try:
        data = response.json()
    except ValueError:
        return None, "bad JSON"

    if must_have not in data:
        return None, "missing " + must_have

    return data, None


def now_text():
    """Current PC time as text, with milliseconds."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def make_row(stamp, data, note=""):
    """Turn one dock answer into one CSV row, in the same order as COLUMNS."""
    if data is None:
        return [stamp, "NO_DATA", "", "", "", "", "", "", note]

    return [
        stamp,
        data["state"],
        data.get("pad_v", ""),
        data.get("relay_closed", ""),
        data.get("robot_present", ""),
        data.get("fault", ""),
        data.get("uptime_ms", ""),
        data.get("boot_count", ""),
        note,
    ]


def open_csv(path, columns=COLUMNS):
    """Open the CSV file to add rows. Write the header only if the file is new."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)

    is_new = not os.path.exists(path) or os.path.getsize(path) == 0

    f = open(path, "a", newline="", encoding="utf-8")
    writer = csv.writer(f)
    if is_new:
        writer.writerow(columns)
        f.flush()
    return f, writer


def build_note(data, error, memory, interval):
    """Decide what to write in the note column of this row.

    memory remembers things between readings:
      "last_good"   -> clock time of the last good reading
      "last_uptime" -> uptime_ms of the last good reading
    """
    if data is None:
        return error

    notes = []
    now = time.monotonic()

    if memory["last_good"] is not None:
        gap = now - memory["last_good"]
        if gap > 1.5 * interval:
            notes.append("gap %.0f s" % gap)
    memory["last_good"] = now

    uptime = data.get("uptime_ms")
    if memory["last_uptime"] is not None and uptime is not None:
        if uptime < memory["last_uptime"]:
            notes.append("DOCK_RESTARTED")
    memory["last_uptime"] = uptime

    return "; ".join(notes)


def new_events(answer, memory):
    """Return only the events we have not saved yet.

    The dock keeps its last 64 events, plus a counter "total" of all events.
    memory["last_total"] remembers that counter from last time.
    """
    events = answer["events"]
    total = answer.get("total", len(events))
    last_total = memory["last_total"]
    memory["last_total"] = total

    if last_total is None or total < last_total:
        return events
    count = total - last_total
    if count == 0:
        return []
    return events[-count:]


def save_events(url, writer, memory):
    """Read /api/events and write the new dock messages to the events CSV."""
    asked_at = datetime.now()
    answer, error = read_status(url, timeout=1.0, must_have="events")
    if answer is None:
        return

    for event in new_events(answer, memory):
        seconds_ago = (answer.get("now_ms", event["ms"]) - event["ms"]) / 1000
        when = asked_at - timedelta(seconds=seconds_ago)
        stamp = when.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        writer.writerow([stamp, event["ms"], event["text"]])
        print("    EVENT", stamp, event["text"])


def record(url, path, events_url, events_path, interval=1.0, minutes=0):
    """Read the dock every `interval` seconds and add one row to the CSV file.
    Every 5 readings, also save the dock's new messages to the events file.
    Runs for `minutes` minutes, or until you press Ctrl+C when minutes is 0."""
    f, writer = open_csv(path)
    ev_f, ev_writer = open_csv(events_path, EVENT_COLUMNS)
    print("Recording", url, "->", path)
    print("Events   ", events_url, "->", events_path)
    print("Press Ctrl+C to stop.")

    rows = 0
    failed = 0
    restarts = 0
    memory = {"last_good": None, "last_uptime": None, "last_total": None}
    next_time = time.monotonic()
    stop_at = next_time + minutes * 60 if minutes else None

    try:
        while stop_at is None or time.monotonic() < stop_at:
            stamp = now_text()
            data, error = read_status(url)
            note = build_note(data, error, memory, interval)
            row = make_row(stamp, data, note)
            writer.writerow(row)
            f.flush()

            rows += 1
            if data is None:
                failed += 1
            if "DOCK_RESTARTED" in note:
                restarts += 1
            print(row[0], row[1], row[2], row[8])

            if rows % 5 == 1 and data is not None:
                save_events(events_url, ev_writer, memory)
                ev_f.flush()

            next_time += interval
            wait = next_time - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            else:
                next_time = time.monotonic()
        print()
        print("Time is up (%g minutes)." % minutes)
    except KeyboardInterrupt:
        print()
        print("Stopped by you.")
    finally:
        f.close()
        ev_f.close()
        print("Rows written:", rows, " failed reads:", failed, " restarts:", restarts)


def main():
    parser = argparse.ArgumentParser(
        description="Record the dock status every second into a CSV file.")
    parser.add_argument("--host", default="127.0.0.1",
                        help="dock address (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8080,
                        help="dock port (default 8080)")
    parser.add_argument("--out", default=None,
                        help="CSV file to write (default: results/dock_<port>_<date>_<time>.csv)")
    parser.add_argument("--interval", type=float, default=1.0,
                        help="seconds between readings (default 1)")
    parser.add_argument("--minutes", type=float, default=0,
                        help="stop after this many minutes (default 0 = run until Ctrl+C)")
    args = parser.parse_args()

    base = "http://%s:%d" % (args.host, args.port)

    out = args.out
    if out is None:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = "results/dock_%d_%s.csv" % (args.port, stamp)
    events_out = os.path.splitext(out)[0] + "_events.csv"

    record(base + "/api/status", out, base + "/api/events", events_out, args.interval, args.minutes)


if __name__ == "__main__":
    main()
