# CSA1516 Assignment 4 Part II - Big Data Engineering: Implement, Test, Secure & Scale
Lohithaksha D | 1921260275 | B.Tech IT | SIMATS Engineering | Faculty: Boomija M D

This folder is separate from Assignment4 (Part I, design only).

## Run
    python3 -m venv .venv && . .venv/bin/activate && pip install numpy pyarrow cryptography
    python run_task1.py   # ... up to run_task6.py (seeds fixed; synthetic data only)
Outputs: `logs/taskN.txt` (console), `results/*.json` (numbers used in the report), `results/predictions.txt` (timestamped predictions written before the runs), `results/quarantine_base.csv`, `results/audit_log.jsonl`.
`part1_events.csv` holds the eight events E1-E8 from my Part I Task 6.

## Environment
Lenovo LOQ 15ARP9, Windows 11, WSL2 Ubuntu 24.04, Python 3.14.4 (8 CPUs and 8.7 GB RAM visible to WSL; library versions are printed at the top of each log).
Assumed: run locally, not on ZOHO/Azure/GCP. Task 1 is a Python multiprocessing map/shuffle/reduce implementation. Task 2 is a Python event-time stream engine (window, watermark, de-duplication). No Spark or Kafka was used.

## Files
common.py | run_task1.py batch pipeline | run_task2.py batch vs stream | run_task3.py security | run_task4.py data quality | run_task5.py storage | run_task6.py fraud-link scalability | show.sh (prints one block of a log)
