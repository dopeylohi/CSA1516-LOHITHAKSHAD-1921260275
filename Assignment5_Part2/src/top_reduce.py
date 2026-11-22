#!/usr/bin/env python3
# Q2 job 2 reducer: one day per key group; keep the N largest stations (ties: smaller station id first)
import sys
N = int(sys.argv[1]) if len(sys.argv) > 1 else 5
cur = None; items = []
def flush():
    for s, c in sorted(items, key=lambda x: (-x[1], x[0]))[:N]: print("%s\t%s\t%d" % (cur, s, c))
for line in sys.stdin:
    day, _, v = line.rstrip("\n").partition("\t"); s, _, c = v.partition(",")
    if not c.isdigit(): continue
    if day != cur:
        if cur is not None: flush()
        cur = day; items = []
    items.append((s, int(c)))
if cur is not None: flush()
