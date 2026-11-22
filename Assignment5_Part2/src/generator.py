#!/usr/bin/env python3
# usage: generator.py OUT SIZE_MB [--seed N] [--hot FRACTION] [--days D] [--bad FRACTION]
# record (assumed): timestamp,station_id,gate_id,card_id,tap_type,fare   (ENTRY fare = 0)
import argparse, random
ap=argparse.ArgumentParser(); ap.add_argument("out"); ap.add_argument("size_mb",type=float)
ap.add_argument("--seed",type=int,default=42); ap.add_argument("--hot",type=float,default=0.0)
ap.add_argument("--days",type=int,default=7); ap.add_argument("--bad",type=float,default=0.0)
a=ap.parse_args(); r=random.Random(a.seed)
st=["S%03d"%i for i in range(1,121)]
ts=["2026-11-%02d %02d:%02d:%02d"%(d+1,h,m,s) for d in range(a.days) for h in range(24) for m in range(60) for s in range(60)]
n=len(ts); target=int(a.size_mb*1024*1024); size=0
with open(a.out,"w") as f:
    while size<target:
        buf=[]
        for _ in range(20000):
            s=st[0] if (a.hot and r.random()<a.hot) else st[r.randrange(120)]
            if a.bad and r.random()<a.bad: buf.append("corrupt,line,%d\n"%r.randrange(1000)); continue
            e=r.random()<0.5
            buf.append("%s,%s,G%d,C%06d,%s,%s\n"%(ts[r.randrange(n)],s,r.randrange(1,9),r.randrange(1000000),"ENTRY" if e else "EXIT","0" if e else "%.2f"%r.uniform(10,60)))
        x="".join(buf); f.write(x); size+=len(x)
