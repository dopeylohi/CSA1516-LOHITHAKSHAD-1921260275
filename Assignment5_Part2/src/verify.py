#!/usr/bin/env python3
# Independent check (no Hadoop): verify.py FILE q1|q2
import sys, collections
c = collections.Counter()
for line in open(sys.argv[1]):
    p = line.rstrip("\r\n").split(",")
    if len(p) != 6 or p[4] != "ENTRY": continue
    ts, st = p[0], p[1]
    c[(st + "|" + ts[:10] + "|" + ts[11:13]) if sys.argv[2] == "q1" else (ts[:10], st)] += 1
if sys.argv[2] == "q1":
    for k in sorted(c): print("%s\t%d" % (k, c[k]))
else:
    days = collections.defaultdict(list)
    for (d, s), n in c.items(): days[d].append((s, n))
    for d in sorted(days):
        for s, n in sorted(days[d], key=lambda x: (-x[1], x[0]))[:5]: print("%s\t%s\t%d" % (d, s, n))
