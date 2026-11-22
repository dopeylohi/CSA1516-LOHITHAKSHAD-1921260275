#!/usr/bin/env python3
# Streaming reducer (also used as combiner): input is SORTED "key<TAB>count" lines; detects key change.
import sys
cur = None; total = 0
for line in sys.stdin:
    k, _, v = line.rstrip("\n").partition("\t")
    try: n = int(v)
    except ValueError: continue
    if k == cur: total += n
    else:
        if cur is not None: print("%s\t%d" % (cur, total))
        cur = k; total = n
if cur is not None: print("%s\t%d" % (cur, total))
