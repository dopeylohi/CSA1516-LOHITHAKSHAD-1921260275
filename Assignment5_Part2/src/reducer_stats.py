#!/usr/bin/env python3
# Per-reducer elapsed time and input records from the JobHistory server: reducer_stats.py JOB_ID
import sys, json, urllib.request as u
base = "http://localhost:19888/ws/v1/history/mapreduce/jobs/" + sys.argv[1]
get = lambda p: json.load(u.urlopen(base + p, timeout=20))
for t in sorted(get("/tasks")["tasks"]["task"], key=lambda t: t["id"]):
    if t["type"] != "REDUCE": continue
    g = get("/tasks/%s/counters" % t["id"])["jobTaskCounters"]["taskCounterGroup"]
    v = {c["name"]: c["value"] for x in g for c in x["counter"]}
    print("%s elapsed_s=%.1f reduce_input_records=%s shuffle_bytes=%s" % (t["id"], t["elapsedTime"]/1000, v.get("REDUCE_INPUT_RECORDS"), v.get("REDUCE_SHUFFLE_BYTES")))
