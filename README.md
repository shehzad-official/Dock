# Dock Recorder (Project 1)

Two small Python programs for the charging dock:

- **`recorder.py`** reads the dock's status once a second and saves every reading to a CSV file.
  It keeps running through Wi-Fi drops and dock restarts, and writes down when they happen.
  It also saves the dock's own messages (`/api/events`) to a second CSV file.
- **`analyze.py`** reads such a CSV file, finds the charge sessions, and saves a session table,
  one chart per session and a short report.

The programs **only read** from the dock (HTTP GET on `/api/status` and `/api/events`).
They never send commands or change settings.

## Files

| File | What it is |
|---|---|
| `recorder.py` | Step 1–3: records the dock every second into a CSV file |
| `analyze.py` | Step 4–5: finds sessions, draws charts, writes `report.md` |
| `results/` | All recordings and analysis made with these programs (see [Results](#results-in-this-repo)) |
| `Dock_Recorder_Report.md` |  project report |
| `requirements.txt` | Python packages needed |
| `dock_simulator.py` | The pretend dock we were given (not changed) |
| `data/recording_A_morning.csv`, `data/recording_B_evening.csv` | The two real recordings we were given (not changed) |
| `Dock_Projects.pdf`, `README.txt` | The project description and start-here notes we were given (not changed) |

## Install

**1. Get the code** and go into its folder:

```
git clone https://github.com/shehzad-official/Dock.git
cd Dock
```

**2. Check Python** (3.8 or newer is needed):

```
python --version
```

**3. Install the packages:**

```
pip install -r requirements.txt
```

On Mac or Linux, use `python3` and `pip3` instead of `python` and `pip`, here and in all the
commands below.

(Tested with Python 3.14, requests 2.34, matplotlib 3.11 on Windows 11.)

## Quick start

Use two terminals, both opened in this folder.

**1. Start the simulator** (terminal 1) and leave it running:

```
python dock_simulator.py data/recording_B_evening.csv
```

To check that it works, open <http://127.0.0.1:8080/api/status> in a browser. You should see the
dock's state as JSON (`state`, `pad_v`, `relay_closed`, …).

**2. Record** (terminal 2). It stops by itself after 15 minutes, or press Ctrl+C to stop earlier:

```
python recorder.py --out results/my_test/my_test.csv --minutes 15
```

It prints one line per reading, for example `2026-11-12 10:00:01.000 CHARGING 29.27`.
At the end it prints `Rows written: …  failed reads: …  restarts: …`.

> **Use a new `--out` name for every recording.** If the file already exists, the recorder adds the
> new rows to the end of it. Do not use the names of the folders that are already in `results/`
> (`A_morning`, `B_evening`, `problem_2h`, …), or your test will be mixed into those results.

**3. Analyze** (terminal 2, after the recording has stopped):

```
python analyze.py results/my_test/my_test.csv
```

This writes `my_test_sessions.csv`, `session_01.png`, … and `report.md` into `results/my_test/`.
Then stop the simulator with Ctrl+C in terminal 1.

## recorder.py

```
python recorder.py [--host 127.0.0.1] [--port 8080] [--out FILE.csv] [--interval 1] [--minutes 0]
```

| Option | Default | Meaning |
|---|---|---|
| `--host` | `127.0.0.1` | Dock address |
| `--port` | `8080` | Dock port |
| `--out` | `results/dock_<port>_<date>_<time>.csv` | CSV file to write. If it already exists, new rows are added at the end |
| `--interval` | `1` | Seconds between readings |
| `--minutes` | `0` | Stop after this many minutes. `0` means run until Ctrl+C |

It writes two files:

- **`<name>.csv`**, one row per reading:
  `time, state, pad_v, relay_closed, robot_present, fault, uptime_ms, boot_count, note`
- **`<name>_events.csv`**, the dock's messages: `time, dock_ms, text`.
  The dock only keeps its last 64 messages, so the recorder asks for them every 5 readings and
  saves only the new ones (it uses the dock's `total` counter to know which are new).

`time` is the PC clock with milliseconds. Every row is written to disk straight away, so nothing is
lost if the program is stopped.

**Why `127.0.0.1` and not `localhost`:** on Windows, `localhost` first tries IPv6, which made every
request take about 2 seconds. `127.0.0.1` answers at once.

### How it deals with problems (Step 3)

| What happens | What the recorder writes | Then |
|---|---|---|
| No answer within 2 s | a `NO_DATA` row, note `timeout` | keeps going |
| Error answer (e.g. HTTP 503) | a `NO_DATA` row, note `HTTP 503` | keeps going |
| Cannot connect / broken answer | a `NO_DATA` row, note `no connection` / `bad JSON` / `missing state` | keeps going |
| First good reading after a pause longer than 1.5 × interval | note `gap N s` | |
| `uptime_ms` is smaller than last time | note `DOCK_RESTARTED` | counts the restart |

At the end it prints `Rows written: …  failed reads: …  restarts: …`.

Readings are taken on a fixed 1-second clock (`time.monotonic()`), so the time between rows does not
slowly grow. After a slow request (for example a 2 s timeout) the clock starts again from now.

## analyze.py

```
python analyze.py CSV_FILE [--outdir FOLDER]
```

It works with files from `recorder.py` and with the original recordings in `data/`.
Output goes to `results/<file name>/` unless `--outdir` is given:

| Output | Contents |
|---|---|
| `<name>_sessions.csv` | session, start_time, end_time, duration_min, start_v, end_v, max_v, readings, longest_gap_s, next_state, warning |
| `session_01.png`, … | pad voltage during each session. The line breaks where there were no readings for more than 3 s. Short sessions also show 15 s before and after, in gray |
| `report.md` | summary, session table, warnings, charts and the rules used |

If the matching `_events.csv` file is next to the CSV, the report also counts the dock messages.

### Rules

- **Session:** starts at the first `CHARGING` reading and ends at the last `CHARGING` reading before
  the state changes to something else. The `state` field is used, not the relay, because the relay
  can open for less than a second during a charge (it did in recording B).
- **`NO_DATA` rows do not end a session.** A Wi-Fi drop or a dock restart in the middle of a charge
  leaves one session, not two.
- **Duration** = time of the last `CHARGING` reading − time of the first.
- **Start V** = pad voltage of the first `CHARGING` reading.
- **End V** = the last reading while the relay was still closed. After the relay opens the robot may
  already be driving away and the pad voltage drops (for example to 1.68 V in recording B), which is
  not the battery voltage.
- **Short charge:** a session under 1 minute is marked `SHORT (< 1 min)`.
  A session still going when the file ends is marked `UNFINISHED`.

## Problem mode and the 2-hour test

Run the first command in terminal 1, and the other two in terminal 2 (one after the other):

```
python dock_simulator.py data/recording_A_morning.csv --port 8092 --drops 0.05 --restart-every 5
python recorder.py --port 8092 --minutes 120 --out results/my_problem_2h/my_problem_2h.csv
python analyze.py results/my_problem_2h/my_problem_2h.csv
```

`--drops 0.05` makes 5 % of requests fail, and `--restart-every 5` restarts the dock every 5 minutes
(offline for 10 s). For a long run, keep the PC plugged in and stop it from going to sleep, and run
it in a normal terminal window that stays open.

Our own 2-hour run in `results/problem_2h/` was made with these same commands, with
`--out results/problem_2h/problem_2h.csv`.

## Several docks

Start one simulator per port and one recorder per simulator. Each command needs its **own terminal**
(4 terminals here):

```
python dock_simulator.py data/recording_A_morning.csv --port 8090
python dock_simulator.py data/recording_B_evening.csv --port 8091
python recorder.py --port 8090 --out results/my_dock_A/my_dock_A.csv
python recorder.py --port 8091 --out results/my_dock_B/my_dock_B.csv
```

Each recorder writes its own files. Our `A_morning`, `B_evening` and `problem_partial_80min` in
`results/` were recorded at the same time from three simulators this way (ports 8090, 8091, 8092).

## Results in this repo

| Folder | What was recorded | Length | Readings | Failed reads | Restarts seen | Sessions |
|---|---|---|---|---|---|---|
| `results/A_morning/` | recording A, normal mode | 10.5 min | 630 | 0 | 0 | 2 |
| `results/B_evening/` | recording B, normal mode | 15.5 min | 930 | 0 | 0 | 1 |
| `results/problem_2h/` | recording A, problem mode, **2 hours** | 120 min | 6879 | 456 | 23 | 24 |
| `results/problem_partial_80min/` | first try of the 2-hour run (see below) | 80 min | 4614 | 287 | 15 | 16 |
| `results/recording_A_morning/`, `results/recording_B_evening/` | `analyze.py` run directly on the original files in `data/`, used to check the recorded results | – | – | – | – | 2 / 1 |

Each folder has the CSV files, the `_console.log` (what the recorder printed) where there is one,
the session table, the charts and `report.md`.

The first 2-hour try stopped after 80 minutes because the terminal it was running in was closed.
The log ends with normal readings and no error, so the recorder did not crash. It was run again for
the full 120 minutes (`problem_2h`), and the first try is kept as extra evidence.

## Known limits

- **One reading per second.** Anything shorter than about 1 s can be missed in the CSV:
  - In recording B the relay opened for 0.45 s. It is not in the status CSV, but the
    `Relay OPENED` / `Relay CLOSED` messages are in `B_evening_events.csv`.
  - Start and end voltages can be off when the voltage changes inside one second
    (B start V: 29.02 recorded vs 26.99 in the original file).
  - A 1.5 s session may be seen in only 1 or 2 readings, so its duration shows as 0–2 s.
- **Times** are PC clock times, accurate to about 1 s. Event times are worked out from the dock's
  `now_ms` and the event's `ms`.
- A restart is detected from `uptime_ms` going down. A restart while the recorder itself is
  stopped is not seen.
