# Dock Recorder Project Report

## 1. Project Overview

We developed two Python scripts, `recorder.py` and `analyze.py`, to monitor and analyze the docking station's charging activity.

The `recorder.py` script retrieves data from the dock's `/api/status` endpoint every second and stores each reading in a CSV file. Additionally, after every five status readings, it retrieves and records new messages from the `/api/events` endpoint.

The recorder operates in read-only mode, meaning it collects and stores information without sending any commands to the docking station.

The `analyze.py` script processes the recorded CSV data to identify charging sessions. It generates a summary table of the detected sessions, an individual chart for each session, and a report containing the analysis results.

## 2. Testing and Results

We tested the application in three test runs, using two simulator configurations (normal and problem mode), to evaluate its performance, reliability, and ability to handle interruptions.

| Test Run | Simulator Configuration | Duration | Total Readings | Failed Reads | Restarts Detected | Sessions |
|---|---|---:|---:|---:|---:|---:|
| Morning (A) | Normal | 10.5 min | 630 | 0 | 0 | 2 |
| Evening (B) | Normal | 15.5 min | 930 | 0 | 0 | 1 |
| Problem Mode (A) | `--drops 0.05 --restart-every 5` | 120 min | 6,879 | 456 | 23 | 24 |

*Source: Our simulator recordings and individual reports stored in `results/<run>/report.md`.*

The application completed the full two-hour test without crashing. Out of the total readings, 456 requests failed, including 304 timeouts and 152 HTTP 503 responses.

Each failed request was recorded as a `NO_DATA` entry, along with the corresponding failure reason. Importantly, these failures did not interrupt the recording process, and the application continued collecting data.

All 23 simulator restarts were successfully detected by monitoring decreases in the `uptime_ms` value. This was consistent with the 24 `Boot` messages recorded in the events file, representing the initial startup and 23 subsequent restarts.

The application identified 24 charging sessions, which matched the expected results. The original 10-minute recording was repeated 12 times, with two charging sessions per repetition.

During our first attempt at the two-hour test, the recording stopped after approximately 80 minutes because the terminal running the process was closed. No application error was recorded in the logs. We repeated the test outside the code editor, and the application successfully completed the full 120-minute recording.

## 3. Charging Session Verification

To verify the accuracy of the analysis, we processed the original recordings using `analyze.py` and compared the generated results with the recordings collected by our application.

| Charging Session | Original Recording | Our Recording |
|---|---|---|
| A – Session 1 | 1.5 s, 28.64 → 29.29 V | 2.0 s, 28.64 → 29.29 V |
| A – Session 2 | 49.0 s, 28.61 → 29.21 V | 49.0 s, 28.61 → 28.62 V |
| B – Session 1 | 13.84 min, 26.99 → 29.41 V | 13.82 min, 29.02 → 29.27 V |

*Source: Original recordings in `data/`, analyzed in `results/recording_A_morning` and `results/recording_B_evening`, compared with our recordings in `results/A_morning` and `results/B_evening`.*

The comparison confirmed that the number of detected charging sessions and their overall durations were consistent with the original recordings.

However, some voltage measurements differed because the application collects status readings at one-second intervals, while voltage levels can change much faster.

For example, in recording B, the voltage increased from 26.99 V to 29.02 V just 0.23 seconds after charging started. This change is visible in `data/recording_B_evening.csv`, between timestamps `17:51:28.369` and `17:51:28.597`.

Since the recorder captures data once per second, its first reading was already 29.02 V. As a result, the initial voltage increase was not captured in the collected status readings.

## 4. Technical Challenges and Solutions

During development and testing, we encountered several scenarios that required careful handling to maintain accurate charging session detection.

### 4.1 Dock Restart During an Active Charging Session

During the two-hour test, charging session 16 started at `01:28:51`. While it was in progress, the dock restarted and was unavailable for 11 seconds (`01:28:59` to `01:29:10`).

Despite this interruption, the charging session was correctly treated as a single continuous session. This is because `NO_DATA` entries are handled as missing readings rather than as indicators that a charging session has ended.

*Source: `results/problem_2h/problem_2h.csv` (rows `01:28:51` to `01:29:10`) and session 16 in `results/problem_2h/report.md`.*

### 4.2 Accurate Final Voltage Measurement

When the relay opens, the robot begins leaving the docking station, causing the charging pad voltage to decrease. In recording B, the voltage dropped to 1.68 V after the relay opened.

To avoid including this post-charging voltage drop in the results, we use the last available voltage reading recorded while the relay was still closed.

*Source: `data/recording_B_evening.csv`, row `18:05:18.633`.*

### 4.3 Brief Relay Interruption

In recording B, the relay briefly opened for 0.45 seconds at `17:56:28`, but the dock's charging state remained `CHARGING`.

To prevent an incorrect session split, our analysis uses the dock's `state` value rather than relying exclusively on the relay status.

The status CSV did not capture this brief interruption because of the one-second sampling interval. However, the events file successfully recorded both `Relay OPENED` and `Relay CLOSED` messages.

*Source: `data/recording_B_evening.csv` (relay open from `17:56:28.349` to `17:56:28.802`) and `results/B_evening/B_evening_events.csv`.*

### 4.4 Localhost Performance on Windows

During testing on Windows, requests made through `localhost` consistently took approximately two seconds to complete.

To avoid this unnecessary delay, we switched to `127.0.0.1` for local API communication.

*Source: our own timing test on the development PC (Windows 11), with the dock simulator running locally.*

## 5. Observations and Data Analysis

The recorded data provided several useful insights into the docking station's charging behaviour.

### 5.1 Morning Recording (A)

Both charging sessions lasted less than one minute and were therefore flagged with a `SHORT` warning.

We also observed frequent transitions into and out of the `BAD_CONTACT` state. The events file recorded seven such messages during the 10-minute recording period.

### 5.2 Evening Recording (B)

The evening recording contained one extended charging session lasting approximately 13.8 minutes.

During this session, the voltage increased from 26.99 V to 29.41 V. However, the robot left the docking station while its state was still `CHARGING`.

Consequently, the charging process did not reach the `CHARGED` state.

*Source: Original recordings stored in `data/` and corresponding events files in `results/`.*

## 6. Limitations and Future Improvements

The current implementation collects one status reading per second. Although this sampling rate is sufficient for monitoring longer charging sessions, it can miss events or voltage changes that occur within shorter intervals.

For example, a charging session lasting 1.5 seconds may appear in only one recorded reading. This can result in an incorrectly calculated duration of 0.0 seconds.

*Source: the 1.5 s session is session 1 in `results/recording_A_morning/report.md`; it was recorded as 0.0 s in sessions 13 and 15 of `results/problem_2h/report.md`.*

To improve measurement accuracy, we would consider introducing a faster sampling rate whenever the dock enters the `CHARGING` state.

We would also use the event timestamps provided by the `/api/events` endpoint to determine the exact start and end times of charging sessions.

Combining higher-frequency status monitoring with event-based timestamps would provide more accurate session durations, improve voltage measurement reliability, and reduce the impact of short-lived events that may otherwise be missed by periodic polling.