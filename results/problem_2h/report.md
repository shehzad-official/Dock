# Dock report: problem_2h

**Source:** `results/problem_2h/problem_2h.csv`, recorded by `recorder.py` from the dock simulator (1 reading per second, so times are accurate to about 1 s).

| | |
|---|---|
| Recorded | 2026-11-12 00:11:41.104 -> 2026-11-12 02:11:40.464 (2.00 h) |
| Readings | 6879 |
| NO_DATA readings | 456 (6.6 %) |
| Dock restarts seen | 23 |
| Charge sessions | 24 |
| Short sessions (< 1 min) | 24 |
| Dock messages (`problem_2h_events.csv`) | 638, incl. 24 x Relay CLOSED, 81 x BAD_CONTACT, 24 x Boot |

## Sessions

| # | Start | End | Duration | Start V | End V | Max V | Readings | Longest gap | Warning |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 00:16:15 | 00:16:16 | 1.0 s | 28.64 | 29.29 | 29.29 | 2 | 1.0 s | SHORT (< 1 min) |
| 2 | 00:19:01 | 00:19:49 | 48.0 s | 28.61 | 28.62 | 29.25 | 48 | 2.0 s | SHORT (< 1 min) |
| 3 | 00:26:12 | 00:26:14 | 2.0 s | 28.64 | 29.29 | 29.29 | 3 | 1.0 s | SHORT (< 1 min) |
| 4 | 00:29:00 | 00:29:48 | 48.1 s | 28.61 | 28.62 | 29.29 | 44 | 3.0 s | SHORT (< 1 min) |
| 5 | 00:36:11 | 00:36:13 | 2.0 s | 28.64 | 29.29 | 29.29 | 3 | 1.0 s | SHORT (< 1 min) |
| 6 | 00:38:57 | 00:39:46 | 49.0 s | 28.61 | 28.62 | 29.29 | 47 | 2.0 s | SHORT (< 1 min) |
| 7 | 00:46:10 | 00:46:11 | 1.0 s | 28.64 | 28.64 | 28.64 | 2 | 1.0 s | SHORT (< 1 min) |
| 8 | 00:48:56 | 00:49:44 | 48.1 s | 28.61 | 28.62 | 28.62 | 46 | 3.0 s | SHORT (< 1 min) |
| 9 | 00:56:08 | 00:56:10 | 2.0 s | 28.64 | 29.29 | 29.29 | 3 | 1.0 s | SHORT (< 1 min) |
| 10 | 00:58:55 | 00:59:43 | 48.0 s | 28.61 | 29.21 | 29.21 | 44 | 3.0 s | SHORT (< 1 min) |
| 11 | 01:06:07 | 01:06:08 | 1.0 s | 28.64 | 29.29 | 29.29 | 2 | 1.0 s | SHORT (< 1 min) |
| 12 | 01:08:53 | 01:09:41 | 48.0 s | 28.61 | 28.62 | 29.25 | 45 | 3.0 s | SHORT (< 1 min) |
| 13 | 01:16:07 | 01:16:07 | 0.0 s | 29.29 | 29.29 | 29.29 | 1 | 0.0 s | SHORT (< 1 min) |
| 14 | 01:18:52 | 01:19:39 | 47.0 s | 28.61 | 28.62 | 28.62 | 47 | 2.0 s | SHORT (< 1 min) |
| 15 | 01:26:05 | 01:26:05 | 0.0 s | 29.29 | 29.29 | 29.29 | 1 | 0.0 s | SHORT (< 1 min) |
| 16 | 01:28:51 | 01:29:39 | 47.1 s | 28.61 | 28.62 | 29.29 | 38 | 11.1 s | SHORT (< 1 min) |
| 17 | 01:36:02 | 01:36:04 | 2.0 s | 28.64 | 29.29 | 29.29 | 3 | 1.0 s | SHORT (< 1 min) |
| 18 | 01:38:48 | 01:39:36 | 48.2 s | 28.61 | 29.21 | 29.21 | 33 | 11.1 s | SHORT (< 1 min) |
| 19 | 01:46:01 | 01:46:03 | 2.0 s | 28.64 | 29.29 | 29.29 | 3 | 1.0 s | SHORT (< 1 min) |
| 20 | 01:48:47 | 01:49:35 | 48.0 s | 28.61 | 28.62 | 28.62 | 44 | 3.0 s | SHORT (< 1 min) |
| 21 | 01:55:59 | 01:56:01 | 2.0 s | 28.64 | 29.29 | 29.29 | 3 | 1.0 s | SHORT (< 1 min) |
| 22 | 01:58:45 | 01:59:33 | 48.1 s | 28.61 | 29.21 | 29.21 | 42 | 3.0 s | SHORT (< 1 min) |
| 23 | 02:05:58 | 02:06:00 | 2.0 s | 28.64 | 29.29 | 29.29 | 3 | 1.0 s | SHORT (< 1 min) |
| 24 | 02:08:44 | 02:09:32 | 48.1 s | 28.61 | 29.21 | 29.21 | 43 | 3.0 s | SHORT (< 1 min) |

## Warnings

- Session 1 (00:16:15, 1.0 s): SHORT (< 1 min)
- Session 2 (00:19:01, 48.0 s): SHORT (< 1 min)
- Session 3 (00:26:12, 2.0 s): SHORT (< 1 min)
- Session 4 (00:29:00, 48.1 s): SHORT (< 1 min)
- Session 5 (00:36:11, 2.0 s): SHORT (< 1 min)
- Session 6 (00:38:57, 49.0 s): SHORT (< 1 min)
- Session 7 (00:46:10, 1.0 s): SHORT (< 1 min)
- Session 8 (00:48:56, 48.1 s): SHORT (< 1 min)
- Session 9 (00:56:08, 2.0 s): SHORT (< 1 min)
- Session 10 (00:58:55, 48.0 s): SHORT (< 1 min)
- Session 11 (01:06:07, 1.0 s): SHORT (< 1 min)
- Session 12 (01:08:53, 48.0 s): SHORT (< 1 min)
- Session 13 (01:16:07, 0.0 s): SHORT (< 1 min)
- Session 14 (01:18:52, 47.0 s): SHORT (< 1 min)
- Session 15 (01:26:05, 0.0 s): SHORT (< 1 min)
- Session 16 (01:28:51, 47.1 s): SHORT (< 1 min)
- Session 17 (01:36:02, 2.0 s): SHORT (< 1 min)
- Session 18 (01:38:48, 48.2 s): SHORT (< 1 min)
- Session 19 (01:46:01, 2.0 s): SHORT (< 1 min)
- Session 20 (01:48:47, 48.0 s): SHORT (< 1 min)
- Session 21 (01:55:59, 2.0 s): SHORT (< 1 min)
- Session 22 (01:58:45, 48.1 s): SHORT (< 1 min)
- Session 23 (02:05:58, 2.0 s): SHORT (< 1 min)
- Session 24 (02:08:44, 48.1 s): SHORT (< 1 min)

## Charts

### Session 1

![Session 1](session_01.png)

### Session 2

![Session 2](session_02.png)

### Session 3

![Session 3](session_03.png)

### Session 4

![Session 4](session_04.png)

### Session 5

![Session 5](session_05.png)

### Session 6

![Session 6](session_06.png)

### Session 7

![Session 7](session_07.png)

### Session 8

![Session 8](session_08.png)

### Session 9

![Session 9](session_09.png)

### Session 10

![Session 10](session_10.png)

### Session 11

![Session 11](session_11.png)

### Session 12

![Session 12](session_12.png)

### Session 13

![Session 13](session_13.png)

### Session 14

![Session 14](session_14.png)

### Session 15

![Session 15](session_15.png)

### Session 16

![Session 16](session_16.png)

### Session 17

![Session 17](session_17.png)

### Session 18

![Session 18](session_18.png)

### Session 19

![Session 19](session_19.png)

### Session 20

![Session 20](session_20.png)

### Session 21

![Session 21](session_21.png)

### Session 22

![Session 22](session_22.png)

### Session 23

![Session 23](session_23.png)

### Session 24

![Session 24](session_24.png)

## How the numbers were made

- A session starts at the first CHARGING reading and ends at the last CHARGING reading. NO_DATA readings (Wi-Fi drops, restarts) do not end a session.
- Start V is the first CHARGING reading. End V is the last reading while the relay was still closed (after it opens, the robot may already be driving away).
- Sessions shorter than 1 minute are marked SHORT.
- Made by `analyze.py` on 2026-11-12 02:12.
