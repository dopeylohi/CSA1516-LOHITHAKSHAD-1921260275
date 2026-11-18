import random, csv, zlib, pickle, time, re, datetime, statistics, math
from collections import Counter, defaultdict
from common import *
R=4; HDR="sensor_id,segment,speed,event_time"; SEGRE=re.compile(r"^S\d\d$")
RULE_DEC={"R1_schema":"reject","R2_bad_key":"reject","R3_missing_speed":"reject","R4_non_numeric":"reject","R5_out_of_range":"reject","R6_bad_time":"reject","R7_normalise_segment":"repair (kept)","R8_duplicate":"reject","OK":"keep"}
def valid_ts(ts):
    try: datetime.datetime.strptime(ts,"%Y-%m-%dT%H:%M:%S"); return True
    except ValueError: return False
def clean_record(line):                    # pure function: returns (decision, rule, reason, record)
    p=line.split(",")
    if len(p)!=4: return "reject","R1_schema",f"expected 4 fields, got {len(p)}",None
    sid,seg,sp,ts=[x.strip() for x in p]; seg2=seg.upper()
    if not sid.isdigit() or not SEGRE.match(seg2): return "reject","R2_bad_key",f"sensor='{sid}' segment='{seg}'",None
    if sp=="": return "reject","R3_missing_speed","speed is empty",None
    try: v=float(sp)
    except ValueError: return "reject","R4_non_numeric",f"speed='{sp}'",None
    if not 0<=v<=200: return "reject","R5_out_of_range",f"speed {v} outside 0-200",None
    if not valid_ts(ts): return "reject","R6_bad_time",f"time='{ts}'",None
    if seg2!=p[1]: return "repair","R7_normalise_segment",f"'{p[1]}' -> '{seg2}'",(sid,seg2,v,ts)
    return "keep","OK","all checks passed",(sid,seg2,v,ts)
def gen(path,total,dup_frac,seed,unit_div=1.0,extra=False):
    rng=random.Random(seed); nb=int(total*(1-dup_frac)); base=[]
    for i in range(nb):
        ts=f"2026-02-0{1+i//86400}T{i%86400//3600:02d}:{i%3600//60:02d}:{i%60:02d}"
        seg=f"S{rng.randint(1,20):02d}"; f=[str(rng.randint(1,500)),seg,f"{rng.uniform(10,90)/unit_div:.1f}",ts]; x=rng.random()
        if x<.02: f[2]=""
        elif x<.03: f[2]="-5"
        elif x<.04: f[2]="999"
        elif x<.05: f=f[:3]
        elif x<.06: f[3]="32/13/2026"
        elif x<.07: f[1]=" "+seg.lower()+" "
        line=",".join(f)
        if extra and len(f)==4: line+=",2"
        base.append(line)
    lines=base+[rng.choice(base) for _ in range(total-nb)]; rng.shuffle(lines)
    open(path,"w").write(HDR+(",lane" if extra else "")+"\n"+"\n".join(lines)+"\n")
def pipeline(path,tag=None):
    t0=time.perf_counter(); parts=[[] for _ in range(R)]; quar=[]; rules=Counter(); trace=defaultdict(list); n_read=0
    with open(path) as f:
        header=f.readline().strip()
        for n,line in enumerate(f,start=2):
            line=line.rstrip("\r\n"); n_read+=1; dec,rule,why,rec=clean_record(line); rules[rule]+=1
            if len(trace[rule])<2: trace[rule].append((n,dec,why,line[:45]))
            if dec=="reject": quar.append((n,rule,why,line)); continue
            parts[zlib.crc32(f"{rec[0]}|{rec[1]}|{rec[3]}".encode())%R].append((n,rec,line,rule))
    sb=sum(len(pickle.dumps(p)) for p in parts); cleaned=[]
    for p in parts:
        seen={}
        for n,rec,line,rule in sorted(p):
            k=(rec[0],rec[1],rec[3])
            if k in seen: rules[rule]-=1; rules["R8_duplicate"]+=1; quar.append((n,"R8_duplicate",f"same sensor/segment/time as line {seen[k]}",line))
            else: seen[k]=n; cleaned.append(rec)
    quar.sort()
    if tag:
        with open(f"{RES}/quarantine_{tag}.csv","w",newline="") as g: w=csv.writer(g); w.writerow(["line_no","rule","reason","raw"]); w.writerows(quar)
        with open(f"{DATA}/cleaned_{tag}.csv","w",newline="") as g: w=csv.writer(g); w.writerow(["sensor_id","segment","speed","event_time"]); w.writerows(cleaned)
    sp=[c[2] for c in cleaned]; seg=defaultdict(list)
    for c in cleaned: seg[c[1]].append(c[2])
    return {"header":header,"read":n_read,"kept":len(cleaned),"quarantined":len(quar),"rules":dict(rules),"shuffle_bytes":sb,"time":time.perf_counter()-t0,
            "mean":statistics.fmean(sp) if sp else None,"sd":statistics.pstdev(sp) if len(sp)>1 else None,
            "segs_below_20":sum(1 for v in seg.values() if statistics.fmean(v)<20),"nseg":len(seg),"trace":dict(trace)}
if __name__=="__main__":
    banner("TASK 4 - ENVIRONMENT"); res={"env":env()}
    gen(f"{DATA}/feed_base.csv",200_000,.05,1)
    runs=[pipeline(f"{DATA}/feed_base.csv","base" if i==2 else None) for i in range(3)]; B=runs[2]; tb=[r["time"] for r in runs]
    banner("4.1 / 4.2 BASELINE (200,000 lines, 5% duplicates)")
    print(f"read {B['read']} | kept {B['kept']} | quarantined {B['quarantined']} | time {fmt(tb)} | shuffle {B['shuffle_bytes']/1024:.0f} KB")
    print("\nDECISION TRACE (2 sample records per rule): line | decision | why | raw")
    for rule,tr in sorted(B["trace"].items()):
        for n,dec,why,raw in tr: print(f"  {rule:<22} line {n:>6} | {dec:<6} | {why} | {raw}")
    print("\nPER-RULE SUMMARY"); print("rule | decision | records")
    for r,c in sorted(B["rules"].items()): print(f"{r:<22} | {RULE_DEC[r]:<13} | {c}")
    print("check: sum of rule counts =",sum(B["rules"].values()),"= lines read",B["read"]); print("quarantine file: results/quarantine_base.csv (line_no, rule, reason, raw)")
    res["base"]={k:v for k,v in B.items() if k!="trace"}; res["base"]["time_runs"]=tb
    shot("4.1/4.2 - totals, decision trace and per-rule table")
    banner("4.3 PREDICT BEFORE EXECUTE: duplicates 5% -> 40% (same 200,000 lines)")
    nb2=int(200_000*.6); pred("4.3",f"Kept falls from {B['kept']} to about {round(B['kept']*nb2/int(200_000*.95))} (unique events shrink from 190,000 to {nb2}). Run time about the same (+-15%) since the same number of lines is read. Shuffle volume about the same (+-5%) since every valid line still goes to the de-dup stage.")
    gen(f"{DATA}/feed_dup.csv",200_000,.40,2); rr=[pipeline(f"{DATA}/feed_dup.csv") for _ in range(3)]; H=rr[2]; th=[r["time"] for r in rr]
    print(f"OBSERVED: kept {H['kept']} | R8_duplicate {H['rules'].get('R8_duplicate')} (was {B['rules'].get('R8_duplicate')}) | time {fmt(th)} (was {fmt(tb)}) | shuffle {H['shuffle_bytes']/1024:.0f} KB (was {B['shuffle_bytes']/1024:.0f} KB)")
    res["dup40"]={"kept":H["kept"],"rules":H["rules"],"time_runs":th,"shuffle_bytes":H["shuffle_bytes"]}; shot("4.3 - prediction line and observed line")
    banner("4.4 SCHEMA DRIFT (speed km/h -> m/s, optionally a new field 'lane')")
    gen(f"{DATA}/drift_a.csv",50_000,.05,11,unit_div=3.6); gen(f"{DATA}/drift_b.csv",50_000,.05,12,unit_div=3.6,extra=True)
    EXPECTED=HDR.split(","); drift={}
    for name,path in (("A: unit change only","drift_a.csv"),("B: unit change + new field","drift_b.csv")):
        D=pipeline(f"{DATA}/{path}")
        print(f"\n[{name}] kept {D['kept']} of {D['read']} | rules {D['rules']}")
        print(f"  mean speed {D['mean']} (baseline {B['mean']:.1f}) | segments with average < 20 'congested': {D['segs_below_20']}/{D['nseg']} (baseline {B['segs_below_20']}/{B['nseg']})")
        hdr_ok=D["header"].split(",")==EXPECTED; z=None
        if D["mean"] is not None: z=(D["mean"]-B["mean"])/(B["sd"]/math.sqrt(D["kept"]))
        print(f"  DEFENCE 1 header check: {'ok' if hdr_ok else 'SCHEMA DRIFT - header is '+D['header']}")
        print(f"  DEFENCE 2 distribution check: z-score of batch mean vs baseline = {z if z is None else round(z,1)} -> {'ALERT (|z|>4)' if z is not None and abs(z)>4 else 'ok'}")
        drift[name]={"kept":D["kept"],"mean":D["mean"],"below20":D["segs_below_20"],"hdr_ok":hdr_ok,"z":z,"rules":D["rules"]}
    res["drift"]=drift; save("task4",res); shot("4.4 - both drift blocks")
