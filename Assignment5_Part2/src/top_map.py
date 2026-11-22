#!/usr/bin/env python3
# Q2 job 2 mapper: "station|day<TAB>count" -> key=day, value="station,count"
import sys
for line in sys.stdin:
    k, _, v = line.rstrip("\n").partition("\t"); st, _, day = k.partition("|"); v = v.strip()
    if day and v.isdigit(): print("%s\t%s,%s" % (day, st, v))
