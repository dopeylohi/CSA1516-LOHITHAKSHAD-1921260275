#!/usr/bin/env python3
# Predicts records per reducer using Hadoop's default HashPartitioner on the Text key (no combiner).
import sys, collections
def jhash(s):
    h = 1
    for b in s.encode(): h = (31*h + b) & 0xFFFFFFFF
    return h & 0x7FFFFFFF
R = int(sys.argv[1])
for f in sys.argv[2:]:
    c = collections.Counter()
    for line in open(f):
        p = line.split(",")
        if len(p) == 6 and p[4] == "ENTRY": c[p[1]+"|"+p[0][:10]+"|"+p[0][11:13]] += 1
    load = [0]*R
    for k, n in c.items(): load[jhash(k) % R] += n
    print("%s: predicted records per reducer %s -> slowest expected: reducer %d (%.1f%% of all records)" % (f.split("/")[-1], load, load.index(max(load)), 100*max(load)/sum(load)))
