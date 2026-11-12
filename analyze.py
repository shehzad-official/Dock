"""
Dock Analyzer: finds the charge sessions in a dock CSV file, draws one chart
per session and writes a short report.

It works with both kinds of file:
  - files made by recorder.py            (results/A_morning/A_morning.csv)
  - the original recordings from the zip (data/recording_B_evening.csv)

Example:
    python analyze.py results/A_morning/A_morning.csv

Output (in results/<file name>/ unless you give --outdir):
    <name>_sessions.csv    table of all sessions
    session_01.png ...     one chart per session (pad voltage over time)
    report.md              short report: summary, sessions table, warnings, charts

Rules used (write these in the README too):
  Session:      starts at the first CHARGING reading and ends at the last
                CHARGING reading before the state changes to something else.
                NO_DATA rows (Wi-Fi drops, dock restarts) do NOT end a session.
  End voltage:  the last reading while the relay was still closed. Just after
                the relay opens, the robot may already be leaving and the
                voltage falls (for example 1.68 V), which is not the battery.
  Short charge: a session shorter than 1 minute gets a warning.
"""
import argparse
import csv
import os
from datetime import datetime, timedelta

import matplotlib
matplotlib.use("Agg")          # save charts to files, never open a window
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

SHORT_LIMIT_MIN = 1.0
CONTEXT_S = 15                  # short sessions: also show 15 s before and after
BREAK_LINE_AFTER_S = 3.0        # no reading for longer than this -> break the line

# Chart colors (one series, so one hue; text stays in ink colors)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#a8a7a1"
GRID = "#e6e5e0"
SERIES = "#2a78d6"

SESSION_COLUMNS = ["session", "start_time", "end_time", "duration_min", "start_v", "end_v",
                   "max_v", "readings", "longest_gap_s", "next_state", "warning"]
TIME_FORMATS = ["%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%H:%M:%S.%f", "%H:%M:%S"]


def parse_time(text):
    """Read a time like '2026-11-11 16:20:34.811' or '11:40:37.336'."""
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    raise ValueError("Unknown time format: " + text)


def time_text(t):
    """Write a time back as text. Original recordings have no date, so show only the clock."""
    if t.year == 1900:
        return t.strftime("%H:%M:%S.%f")[:-3]
    return t.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def duration_text(minutes):
    """13.84 -> '13.84 min', and 0.82 -> '49.0 s' (short ones read better in seconds)."""
    if minutes < 1:
        return "%.1f s" % (minutes * 60)
    return "%.2f min" % minutes


def to_float(text):
    """'28.61' -> 28.61, and '' -> None (NO_DATA rows have no voltage)."""
    if text is None or text == "":
        return None
    return float(text)


def load_rows(path):
    """Read a dock CSV file into a list of simple dicts."""
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            relay = r.get("relay_closed", r.get("relay", ""))
            rows.append({
                "time": parse_time(r["time"]),
                "state": r["state"],
                "pad_v": to_float(r.get("pad_v")),
                "relay": relay == "True",
                "note": r.get("note", "") or "",
            })
    if not rows:
        raise SystemExit("The file has no data rows: " + path)
    return rows


def make_session(number, charging, next_row):
    """Build one session (a dict) from its CHARGING readings."""
    first, last = charging[0], charging[-1]
    duration_min = (last["time"] - first["time"]).total_seconds() / 60

    with_relay = [r for r in charging if r["relay"]]
    end_row = with_relay[-1] if with_relay else last

    volts = [r["pad_v"] for r in charging if r["pad_v"] is not None]
    gaps = [(b["time"] - a["time"]).total_seconds() for a, b in zip(charging, charging[1:])]

    if next_row is None:
        warning = "UNFINISHED (file ends while charging)"
    elif duration_min < SHORT_LIMIT_MIN:
        warning = "SHORT (< 1 min)"
    else:
        warning = ""

    return {
        "session": number,
        "start_time": first["time"],
        "end_time": last["time"],
        "duration_min": duration_min,
        "start_v": first["pad_v"],
        "end_v": end_row["pad_v"],
        "max_v": max(volts) if volts else None,
        "readings": len(charging),
        "longest_gap_s": max(gaps) if gaps else 0.0,
        "next_state": next_row["state"] if next_row else "",
        "warning": warning,
    }


def find_sessions(rows):
    """Walk through the readings and cut out every CHARGING session."""
    sessions = []
    charging = []

    for row in rows:
        if row["state"] == "NO_DATA":
            continue
        if row["state"] == "CHARGING":
            charging.append(row)
        elif charging:
            sessions.append(make_session(len(sessions) + 1, charging, row))
            charging = []

    if charging:
        sessions.append(make_session(len(sessions) + 1, charging, None))
    return sessions


def save_sessions(sessions, path):
    """Write the sessions table to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(SESSION_COLUMNS)
        for s in sessions:
            writer.writerow([
                s["session"],
                time_text(s["start_time"]),
                time_text(s["end_time"]),
                "%.2f" % s["duration_min"],
                s["start_v"],
                s["end_v"],
                s["max_v"],
                s["readings"],
                "%.1f" % s["longest_gap_s"],
                s["next_state"],
                s["warning"],
            ])


def print_summary(path, rows, sessions):
    """Show the results on the screen."""
    no_data = sum(1 for r in rows if r["state"] == "NO_DATA")
    restarts = sum(1 for r in rows if "DOCK_RESTARTED" in r["note"])

    print("File:      ", path)
    print("From / to: ", time_text(rows[0]["time"]), "->", time_text(rows[-1]["time"]))
    print("Readings:  ", len(rows), "  NO_DATA:", no_data, "  restarts:", restarts)
    print("Sessions:  ", len(sessions))
    print()
    print("%-3s %-23s %-23s %8s %8s %8s  %s" % ("#", "start", "end", "minutes", "start V", "end V", "warning"))
    for s in sessions:
        print("%-3d %-23s %-23s %8.2f %8s %8s  %s" % (
            s["session"], time_text(s["start_time"]), time_text(s["end_time"]),
            s["duration_min"], s["start_v"], s["end_v"], s["warning"]))


def with_breaks(readings):
    """x and y lists for plotting. A long gap between two readings breaks the line,
    so the chart never draws a line through time when we had no data."""
    xs, ys = [], []
    for i, r in enumerate(readings):
        if i > 0 and (r["time"] - readings[i - 1]["time"]).total_seconds() > BREAK_LINE_AFTER_S:
            xs.append(r["time"])
            ys.append(float("nan"))
        xs.append(r["time"])
        ys.append(r["pad_v"])
    return xs, ys


def draw_chart(rows, s, path):
    """One chart for one session: pad voltage over time."""
    start, end = s["start_time"], s["end_time"]
    short = (end - start).total_seconds() < 20
    pad = timedelta(seconds=CONTEXT_S) if short else timedelta(0)

    window = [r for r in rows if start - pad <= r["time"] <= end + pad and r["pad_v"] is not None]
    in_session = [r for r in window if start <= r["time"] <= end and r["state"] == "CHARGING"]

    # Y range from the readings with the charger connected. A reading taken while
    # the robot drives off (relay open, voltage falling) would squash the chart.
    focus = [r["pad_v"] for r in window if r["relay"]] or [r["pad_v"] for r in window]
    low, high = min(focus), max(focus)
    margin = max(0.1, (high - low) * 0.15)
    y_low, y_high = low - margin, high + margin
    off_scale = [r["pad_v"] for r in in_session if not y_low <= r["pad_v"] <= y_high]
    context_cut = any(not y_low <= r["pad_v"] <= y_high for r in window)

    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=120)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    markers = "o" if len(window) <= 120 else None
    if short:
        xs, ys = with_breaks(window)
        ax.plot(xs, ys, color=MUTED, linewidth=1.5, marker=markers, markersize=4)
        ax.axvspan(start, end, color=SERIES, alpha=0.08, linewidth=0)
        ax.text(start, y_high, " CHARGING", color=INK_2, fontsize=8, va="top")
    xs, ys = with_breaks(in_session)
    ax.plot(xs, ys, color=SERIES, linewidth=2, marker=markers, markersize=5)

    ax.set_ylim(y_low, y_high)
    ax.set_ylabel("Pad voltage (V)", color=INK_2)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    ax.grid(axis="y", color=GRID, linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK_2, labelsize=8)

    ax.set_title("Session %d: pad voltage while charging" % s["session"],
                 loc="left", color=INK, fontsize=12, fontweight="bold", pad=22)
    details = "%s -> %s  |  %s  |  %s V -> %s V" % (
        s["start_time"].strftime("%H:%M:%S"), s["end_time"].strftime("%H:%M:%S"),
        duration_text(s["duration_min"]), s["start_v"], s["end_v"])
    if s["longest_gap_s"] > BREAK_LINE_AFTER_S:
        details += "  |  longest gap %.0f s" % s["longest_gap_s"]
    if s["warning"]:
        details += "  |  " + s["warning"]
    ax.text(0, 1.02, details, transform=ax.transAxes, color=INK_2, fontsize=8.5)

    if short:
        note = "Gray: readings %d s before and after the session" % CONTEXT_S
        if context_cut:
            note += " (some are off scale)"
        ax.text(0, -0.16, note, transform=ax.transAxes, ha="left", color=INK_2, fontsize=7.5)
    if off_scale:
        ax.text(1, -0.16, "%d session reading(s) off scale, lowest %.2f V (robot leaving, relay open)"
                % (len(off_scale), min(off_scale)),
                transform=ax.transAxes, ha="right", color=INK_2, fontsize=7.5)

    fig.tight_layout()
    fig.savefig(path, facecolor=SURFACE)
    plt.close(fig)


def count_events(events_path):
    """Count a few useful kinds of dock messages in the events CSV (if there is one)."""
    if not os.path.exists(events_path):
        return None
    with open(events_path, newline="", encoding="utf-8") as f:
        texts = [r["text"] for r in csv.DictReader(f)]
    return {
        "total": len(texts),
        "relay_closed": sum(1 for t in texts if t == "Relay CLOSED"),
        "boots": sum(1 for t in texts if t.startswith("Boot")),
        "bad_contact": sum(1 for t in texts if "-> BAD_CONTACT" in t),
        "events_file": os.path.basename(events_path),
    }


def write_report(path, source, rows, sessions, chart_files, events):
    """Write report.md: summary, sessions table, warnings and charts."""
    no_data = sum(1 for r in rows if r["state"] == "NO_DATA")
    restarts = sum(1 for r in rows if "DOCK_RESTARTED" in r["note"])
    hours = (rows[-1]["time"] - rows[0]["time"]).total_seconds() / 3600
    original = rows[0]["time"].year == 1900

    lines = []
    lines.append("# Dock report: %s" % os.path.splitext(os.path.basename(source))[0])
    lines.append("")
    if original:
        lines.append("**Source:** original dock recording `%s` (about 4 readings per second)." % source)
    else:
        lines.append("**Source:** `%s`, recorded by `recorder.py` from the dock simulator "
                     "(1 reading per second, so times are accurate to about 1 s)." % source)
    lines.append("")
    lines.append("| | |")
    lines.append("|---|---|")
    lines.append("| Recorded | %s -> %s (%.2f h) |" % (time_text(rows[0]["time"]), time_text(rows[-1]["time"]), hours))
    lines.append("| Readings | %d |" % len(rows))
    lines.append("| NO_DATA readings | %d (%.1f %%) |" % (no_data, 100.0 * no_data / len(rows)))
    lines.append("| Dock restarts seen | %d |" % restarts)
    lines.append("| Charge sessions | %d |" % len(sessions))
    lines.append("| Short sessions (< 1 min) | %d |" % sum(1 for s in sessions if s["warning"].startswith("SHORT")))
    if events:
        lines.append("| Dock messages (`%s`) | %d, incl. %d x Relay CLOSED, %d x BAD_CONTACT, %d x Boot |"
                     % (events["events_file"], events["total"], events["relay_closed"],
                        events["bad_contact"], events["boots"]))
    lines.append("")

    lines.append("## Sessions")
    lines.append("")
    if sessions:
        lines.append("| # | Start | End | Duration | Start V | End V | Max V | Readings | Longest gap | Warning |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for s in sessions:
            lines.append("| %d | %s | %s | %s | %s | %s | %s | %d | %.1f s | %s |" % (
                s["session"], s["start_time"].strftime("%H:%M:%S"), s["end_time"].strftime("%H:%M:%S"),
                duration_text(s["duration_min"]), s["start_v"], s["end_v"], s["max_v"],
                s["readings"], s["longest_gap_s"], s["warning"]))
    else:
        lines.append("No charge sessions in this file.")
    lines.append("")

    warnings = [s for s in sessions if s["warning"]]
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for s in warnings:
            lines.append("- Session %d (%s, %s): %s" % (
                s["session"], s["start_time"].strftime("%H:%M:%S"),
                duration_text(s["duration_min"]), s["warning"]))
        lines.append("")

    if chart_files:
        lines.append("## Charts")
        lines.append("")
        for s, chart in zip(sessions, chart_files):
            lines.append("### Session %d" % s["session"])
            lines.append("")
            lines.append("![Session %d](%s)" % (s["session"], chart))
            lines.append("")

    lines.append("## How the numbers were made")
    lines.append("")
    lines.append("- A session starts at the first CHARGING reading and ends at the last CHARGING reading. "
                 "NO_DATA readings (Wi-Fi drops, restarts) do not end a session.")
    lines.append("- Start V is the first CHARGING reading. End V is the last reading while the relay was "
                 "still closed (after it opens, the robot may already be driving away).")
    lines.append("- Sessions shorter than 1 minute are marked SHORT.")
    lines.append("- Made by `analyze.py` on %s." % datetime.now().strftime("%Y-%m-%d %H:%M"))
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(
        description="Find the charge sessions in a dock CSV file, draw charts and write a report.")
    parser.add_argument("csv_file", help="CSV from recorder.py, or an original recording")
    parser.add_argument("--outdir", default=None,
                        help="folder for the results (default: results/<file name>/)")
    args = parser.parse_args()

    name = os.path.splitext(os.path.basename(args.csv_file))[0]
    outdir = args.outdir or os.path.join("results", name)
    os.makedirs(outdir, exist_ok=True)

    rows = load_rows(args.csv_file)
    sessions = find_sessions(rows)

    sessions_path = os.path.join(outdir, name + "_sessions.csv")
    save_sessions(sessions, sessions_path)

    chart_files = []
    for s in sessions:
        chart = "session_%02d.png" % s["session"]
        draw_chart(rows, s, os.path.join(outdir, chart))
        chart_files.append(chart)

    events = count_events(os.path.splitext(args.csv_file)[0] + "_events.csv")
    report_path = os.path.join(outdir, "report.md")
    write_report(report_path, args.csv_file, rows, sessions, chart_files, events)

    print_summary(args.csv_file, rows, sessions)
    print()
    print("Saved:", sessions_path)
    print("Saved:", len(chart_files), "chart(s) and", report_path)


if __name__ == "__main__":
    main()
