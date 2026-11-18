import os, json, time, zlib, pickle, random, multiprocessing as mp
from collections import defaultdict
import numpy as np
from common import *
SEGS,HOURS,R,M=50,48,4,8   # segments, hours of data, reducers, mappers

def gen(path,n,seed=1,bad=0.03):
    rng=np.random.default_rng(seed)
    sid=rng.integers(1,501,n).tolist(); seg=rng.integers(1,SEGS+1,n).tolist()
    sp=np.round(rng.normal(45,12,n).clip(5,120),1).tolist()
    t=rng.integers(0,HOURS*3600,n).tolist(); u=rng.random(n).tolist(); nbad=0
    with open(path,"w") as f:
        f.write("sensor_id,segment,speed,event_time\n")
        for i in range(n):
            ts=f"2026-01-0{1+t[i]//86400}T{t[i]%86400//3600:02d}:{t[i]%3600//60:02d}:{t[i]%60:02d}"
            x=u[i]; s=sp[i]
            if x<bad/3: s=""
            elif x<2*bad/3: s="-1" if i%2 else "999"
            elif x<bad: f.write(f"{sid[i]},S{seg[i]:02d},{s}\n"); nbad+=1; continue
            if x<2*bad/3: nbad+=1
            f.write(f"{sid[i]},S{seg[i]:02d},{s},{ts}\n")
    return nbad

def parse_line(line):                      # pure function: no I/O
    p=line.split(",")
    if len(p)!=4: return None,"malformed"
    try: v=float(p[2])
    except ValueError: return None,"null_speed"
    if not 0<=v<=200: return None,"bad_speed"
    ts=p[3]
    if len(ts)!=19 or ts[10]!="T": return None,"bad_time"
    return ((p[1],ts[:13]),v),None

def mapper(a):
    path,start,end=a; t0=time.perf_counter(); loc={}; rej=defaultdict(int); read=0
    with open(path,"rb") as f:
        if start==0: pos=len(f.readline())
        else: f.seek(start-1); pos=start-1+len(f.readline())
        for raw in iter(f.readline,b""):
            if pos>=end: break
            pos+=len(raw); read+=1
            kv,err=parse_line(raw.decode().rstrip("\r\n"))
            if err: rej[err]+=1; continue
            k,v=kv; c=loc.get(k)
            if c: c[0]+=v; c[1]+=1
            else: loc[k]=[v,1]
    parts=[{} for _ in range(R)]
    for k,c in loc.items(): parts[zlib.crc32(f"{k[0]}|{k[1]}".encode())%R][k]=c
    return {"read":read,"acc":sum(c[1] for c in loc.values()),"rej":dict(rej),"parts":parts,"t":time.perf_counter()-t0}

def run_job(path,m=M):
    size=os.path.getsize(path); cuts=[size*i//m for i in range(m+1)]; T={}
    t=time.perf_counter()
    with mp.Pool(min(m,os.cpu_count())) as p: res=p.map(mapper,[(path,cuts[i],cuts[i+1]) for i in range(m)])
    T["map"]=time.perf_counter()-t
    t=time.perf_counter(); inbox=[[] for _ in range(R)]; sb=0; sp_=0
    for r in res:
        for i,part in enumerate(r["parts"]): sb+=len(pickle.dumps(part)); sp_+=len(part); inbox[i].append(part)
    T["shuffle"]=time.perf_counter()-t
    t=time.perf_counter(); out={}; load=[]
    for i in range(R):
        acc={}; n=0
        for part in inbox[i]:
            for k,c in part.items():
                n+=c[1]; a=acc.get(k)
                if a: a[0]+=c[0]; a[1]+=c[1]
                else: acc[k]=[c[0],c[1]]
        load.append({"reducer":i,"keys":len(acc),"records":n})
        for k,c in acc.items(): out[k]=c[0]/c[1]
    T["reduce"]=time.perf_counter()-t
    rej=defaultdict(int)
    for r in res:
        for k,v in r["rej"].items(): rej[k]+=v
    return out,{"read":sum(r["read"] for r in res),"accepted":sum(r["acc"] for r in res),"rejected":dict(rej),
        "per_mapper_records":[r["read"] for r in res],"per_mapper_s":[round(r["t"],3) for r in res],
        "shuffle_pairs":sp_,"shuffle_bytes":sb,"reducer_load":load,"stage_s":T}

def reference(path):                       # independent single-process version (csv module)
    import csv, statistics
    d=defaultdict(list); acc=rej=0
    with open(path,newline="") as f:
        rd=csv.reader(f); next(rd)
        for row in rd:
            try:
                if len(row)!=4: raise ValueError
                v=float(row[2])
                if not 0<=v<=200 or len(row[3])!=19: raise ValueError
            except ValueError: rej+=1; continue
            d[(row[1],row[3][:13])].append(v); acc+=1
    return {k:statistics.fmean(v) for k,v in d.items()},acc,rej

def compare(out,ref):
    if set(out)!=set(ref): return False,None
    return True,max((abs(out[k]-ref[k]) for k in ref),default=0.0)

TINY="""sensor_id,segment,speed,event_time
1,S01,40.0,2026-01-01T00:10:00
2,S01,50.0,2026-01-01T00:20:00
3,S02,30.0,2026-01-01T01:05:00
4,S03,,2026-01-01T01:06:00
5,S03,-1,2026-01-01T01:07:00
6,S04,45.5,2026-01-01T02:00:00
7,S04
8,S05,60.0,2026-01-01T03:00:00
"""
if __name__=="__main__":
    banner("TASK 1 - ENVIRONMENT"); res={"env":env()}
    sizes={"200k":200_000,"1M":1_000_000,"5M":5_000_000}
    pred("1.3","Dominant stage stays MAP at all sizes (every line is parsed). Shuffle pairs stay roughly constant (<= 8 mappers x 2400 keys = 19,200) because each mapper pre-adds locally. Run time grows about linearly with events.")
    paths={};truth={}
    for k,n in sizes.items():
        paths[k]=f"{DATA}/traffic_{k}.csv"; truth[k]=gen(paths[k],n)
    res["generator_truth_bad_rows"]=truth
    banner("1.1 SAMPLE: pipeline vs single-process reference (first 20,000 events)")
    sample=f"{DATA}/sample.csv"
    with open(paths["200k"]) as f, open(sample,"w") as g:
        for i,l in enumerate(f):
            if i>20000: break
            g.write(l)
    out,s=run_job(sample); ref,racc,rrej=reference(sample); ok,d=compare(out,ref)
    print("pipeline: read",s["read"],"accepted",s["accepted"],"rejected",s["rejected"])
    print("reference: accepted",racc,"rejected",rrej)
    print("per-mapper records:",s["per_mapper_records"]); print("per-reducer load:",s["reducer_load"])
    print("first 5 averages (segment,hour)->km/h:",[(k,round(v,2)) for k,v in sorted(out.items())[:5]])
    print("IDENTICAL KEYS:",ok,"| max abs difference:",d)
    res["sample"]={"stats":s,"ref_acc":racc,"ref_rej":rrej,"identical":ok,"maxdiff":d}
    shot("1.1 - everything printed above")
    banner("1.2 / 1.3 SCALED RUNS (3 runs each)"); rows=[]
    for k,p in paths.items():
        ts=[]
        for _ in range(3):
            t=time.perf_counter(); o,s=run_job(p); ts.append(time.perf_counter()-t)
        dom=max(s["stage_s"],key=s["stage_s"].get)
        print(f"\n[{k}] file {os.path.getsize(p)/1e6:.1f} MB | read {s['read']} accepted {s['accepted']} rejected {sum(s['rejected'].values())} {s['rejected']} (generator truth bad={truth[k]})")
        print(f"  total {fmt(ts)} | stages(s) {({a:round(b,3) for a,b in s['stage_s'].items()})} | dominant: {dom}")
        print(f"  partitions: {M} map tasks, {R} reducers | shuffle {s['shuffle_pairs']} pairs, {s['shuffle_bytes']/1024:.1f} KB | per-mapper s {s['per_mapper_s']}")
        print(f"  reducer load {s['reducer_load']}")
        rows.append({"size":k,"events":sizes[k],"runs_s":ts,"stage_s":s["stage_s"],"dominant":dom,"shuffle_pairs":s["shuffle_pairs"],"shuffle_bytes":s["shuffle_bytes"],"read":s["read"],"accepted":s["accepted"],"rejected":s["rejected"],"reducer_load":s["reducer_load"],"per_mapper_s":s["per_mapper_s"]})
    base=rows[0]; print("\nPREDICTION vs OBSERVATION")
    for r in rows: print(f"  {r['size']}: events x{r['events']/base['events']:.0f} | time x{sum(r['runs_s'])/sum(base['runs_s']):.1f} | shuffle pairs {r['shuffle_pairs']} | dominant {r['dominant']}")
    res["scaled"]=rows; shot("1.2/1.3 - the 3 size blocks and the prediction-vs-observation lines")
    banner("1.4 BOUNDARY TESTS"); bd={}
    tp=f"{DATA}/tiny.csv"; open(tp,"w").write(TINY)
    out,s=run_job(tp); ref,racc,rrej=reference(tp); ok,d=compare(out,ref)
    print("TINY file (8 mappers on ~10 lines; S05 single record; S03 only bad speeds; one short line)")
    print(" per-mapper records:",s["per_mapper_records"],"(zeros = empty partitions)")
    print(" reducer load:",s["reducer_load"],"| rejected:",s["rejected"])
    print(" output:",{k:round(v,2) for k,v in sorted(out.items())}); print(" matches reference:",ok,"diff",d)
    bd["tiny"]={"per_mapper":s["per_mapper_records"],"reducers":s["reducer_load"],"rejected":s["rejected"],"ok":ok}
    sp=f"{DATA}/skew.csv"; rng=random.Random(9)
    with open(sp,"w") as f:
        f.write("sensor_id,segment,speed,event_time\n")
        for i in range(200_000):
            seg="S01" if rng.random()<0.9 else f"S{rng.randint(2,50):02d}"
            sv="" if rng.random()<0.01 else f"{rng.uniform(10,90):.1f}"
            f.write(f"{rng.randint(1,500)},{seg},{sv},2026-01-01T{rng.randint(0,23):02d}:00:00\n")
        f.write("1,S99,33.3,2026-01-01T05:00:00\n")
    out,s=run_job(sp); ref,racc,rrej=reference(sp); ok,d=compare(out,ref)
    tot=sum(r["records"] for r in s["reducer_load"]); mx=max(r["records"] for r in s["reducer_load"])
    print("\nSKEW file (90% of events in S01, 1% null speeds, S99 has one record)")
    print(" reducer load:",s["reducer_load"],f"| busiest reducer holds {100*mx/tot:.1f}% of records")
    print(" S99 present:",any(k[0]=="S99" for k in out),"| matches reference:",ok,"diff",d,"| rejected",s["rejected"])
    bd["skew"]={"reducers":s["reducer_load"],"busiest_pct":100*mx/tot,"ok":ok,"rejected":s["rejected"]}
    res["boundary"]=bd; save("task1",res); shot("1.4 - both boundary blocks")
