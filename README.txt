DOCK PROJECTS - START HERE
==========================

What is in this zip
-------------------
Dock_Projects.pdf              The two projects: what to do, what to hand in, how we mark it.
dock_simulator.py              A pretend dock that runs on your laptop (Project 1).
data/recording_A_morning.csv   Real recording from our dock, 10 minutes (11:40 to 11:50).
data/recording_B_evening.csv   Real recording from our dock, 15 minutes (17:50 to 18:05).

You need
--------
Python 3.8 or newer. Nothing else for the simulator.
For your own program you will probably also want:  pip install requests matplotlib

Start the simulator
-------------------
Open a terminal in this folder and run:

    python dock_simulator.py data/recording_B_evening.csv

Then open this address in your browser:

    http://localhost:8080/api/status     (the dock's state right now)
    http://localhost:8080/api/events     (the dock's recent messages)

Leave the terminal open while you work. Press Ctrl+C to stop the simulator.

Useful options
--------------
--speed 10                 play 10 times faster (good for quick tests)
--drops 0.05               5 % of requests fail, like bad Wi-Fi
--restart-every 5          the dock "restarts" every 5 minutes (offline for 10 s)
--port 8081                use another port, so you can run two docks at once

Problem mode for Step 3 and the 2-hour test:

    python dock_simulator.py data/recording_A_morning.csv --drops 0.05 --restart-every 5

The recording plays from start to end and then repeats.

Recording columns (CSV)
-----------------------
time            clock time of the sample (hh:mm:ss.mmm)
state           what the dock was doing (IDLE, STABILIZING, CHARGING, ...)
relay           True when the charger was connected to the pads
pad_v           voltage on the pads, in volts
robot_present   True when a robot battery was seen on the pads
fault           error text, empty when everything was fine

Rules
-----
Your program only reads data. It never sends commands.
Write down where every number in your report comes from.
Ask your supervisor when you are stuck.
