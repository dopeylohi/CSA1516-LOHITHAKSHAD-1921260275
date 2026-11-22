#!/usr/bin/env python3
# Q1 mapper (hour) / Q2 job-1 mapper (day). Parses, validates, keeps ENTRY only, counts bad records.
import os, sys
mode = sys.argv[1] if len(sys.argv) > 1 else "hour"
FAIL = os.environ.get("FAIL_MODE", "none")                      # test hook for Task B4.1 only
ATT = os.environ.get("mapreduce_task_attempt_id", "")
bad = exits = 0; out = []
for line in sys.stdin:
    if FAIL != "none" and ",CFAIL," in line and (FAIL == "permanent" or ATT.endswith("_0")):
        sys.stderr.write("FAULT INJECTED on record %s in %s\n" % (line.strip(), ATT)); sys.exit(1)
    p = line.rstrip("\r\n").split(",")
    if len(p) != 6: bad += 1; continue
    ts, st, gate, card, tap, fare = p
    try:
        float(fare)
        if len(ts) != 19 or not st or tap not in ("ENTRY", "EXIT"): raise ValueError
        int(ts[11:13])
    except ValueError:
        bad += 1; continue
    if tap != "ENTRY": exits += 1; continue
    out.append(st + "|" + ts[:10] + ("|" + ts[11:13] if mode == "hour" else "") + "\t1\n")
    if len(out) >= 50000: sys.stdout.write("".join(out)); out = []
sys.stdout.write("".join(out))
sys.stderr.write("reporter:counter:Q1,MalformedRecords,%d\n" % bad)
sys.stderr.write("reporter:counter:Q1,ExitTapsSkipped,%d\n" % exits)
