import sys, json, time, random, subprocess, resource
from collections import defaultdict, deque
from common import *
WIN=7
ASSUMED_8=[("A1","B1",1),("A1","B2",3),("A1","B3",6),("A2","B1",1),("A2","B2",2),("A2","B1",9),("A3","B4",2),("A3","B5",10)]  # ASSUMED - replace via part1_events.csv
H20=[("A","B1",1),("A","B2",3),("A","B3",7),("B","B1",1),("B","B2",3),("B","B3",8),("C","B1",2),("C","B1",3),("C","B1",4),("C","B2",5),
     ("D","B4",10),("D","B5",11),("D","B6",12),("D","B7",13),("E","B1",1),("E","B2",2),("E","B3",20),("F","B8",5),("F","B9",5),("F","B10",5)]
HAND_EXPECTED={"A","D","F"}   # derived by hand before running (see report)
def naive(ev):                              # compares every event with every other event: n*n comparisons
    flagged=defaultdict(set)
    for a,b,d in ev:
        win=[(b2,d2) for a2,b2,d2 in ev if a2==a and 0<=d2-d<WIN]
        if len({x[0] for x in win})>=3: flagged[a].update(win)
    return dict(flagged),len(ev)*len(ev)
def keyed(ev,detail=True):                  # group by account, sliding 7-day window per account
    g=defaultdict(list)
    for a,b,d in ev: g[a].append((d,b))
    flagged={}; proc=0; peak=0
    for a,lst in g.items():
        lst.sort(); dq=deque(); cnt={}; fd=set()
        for d,b in lst:
            proc+=1
            while dq and dq[0][0]<=d-WIN:
                ob=dq.popleft()[1]; cnt[ob]-=1
                if not cnt[ob]: del cnt[ob]
            dq.append((d,b)); cnt[b]=cnt.get(b,0)+1
            if len(cnt)>=3: fd.add(d)
            if len(dq)>peak: peak=len(dq)
        if fd:
            if detail:
                cover=set()
                for e in fd: cover.update(range(e-WIN+1,e+1))
                flagged[a]={(b,d) for d,b in lst if d in cover}
            else: flagged[a]=None
    return flagged,proc,peak
def show(f):
    for a in sorted(f): print(f"   account {a}: beneficiaries {sorted({b for b,_ in f[a]})} days {sorted({d for _,d in f[a]})}")
    if not f: print("   (none flagged)")
def gen_arrays(n,skew,seed=3):
    import numpy as np
    r=np.random.default_rng(seed); a=r.integers(0,max(n//10,1),n); b=r.integers(0,5000,n); d=r.integers(0,60,n)
    if skew: a[:int(skew*n)]=0
    return a,b,d
def gen(n,skew):
    a,b,d=gen_arrays(n,skew); return list(zip(a.tolist(),b.tolist(),d.tolist()))
def child(method,n,skew):
    ev=gen(n,skew); t=time.perf_counter()
    if method=="naive": f,proc=naive(ev); peak=None
    else: f,proc,peak=keyed(ev,False)
    print("RESULT"+json.dumps({"s":time.perf_counter()-t,"flagged":len(f),"proc":proc,"peak":peak,"rss_mb":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024}))
def run_child(method,n,skew=0):
    p=subprocess.run([sys.executable,__file__,"--one",method,str(n),str(skew)],capture_output=True,text=True)
    for l in p.stdout.splitlines():
        if l.startswith("RESULT"): return json.loads(l[6:])
    return {"failed":True,"returncode":p.returncode}
if __name__=="__main__":
    if len(sys.argv)>1 and sys.argv[1]=="--one": child(sys.argv[2],int(sys.argv[3]),float(sys.argv[4])); sys.exit()
    banner("TASK 6 - ENVIRONMENT"); res={"env":env()}
    banner("6.3 THE EIGHT EVENTS FROM PART I")
    try: ev8=[(a,b,int(d)) for a,b,d in (l.strip().split(",") for l in open("part1_events.csv") if l.strip() and not l.startswith("account"))]; print("using part1_events.csv")
    except FileNotFoundError: ev8=ASSUMED_8; print("part1_events.csv not found -> using ASSUMED events")
    print("events (account,beneficiary,day):",ev8); fn,cn=naive(ev8); fk,pk,_=keyed(ev8)
    print("NAIVE flagged:"); show(fn); print("KEYED flagged:"); show(fk); print("agree:",fn==fk); res["eight"]={"events":ev8,"naive":{a:sorted(v) for a,v in fn.items()},"keyed":{a:sorted(v) for a,v in fk.items()},"agree":fn==fk}
    shot("6.3 - the eight-event block")
    banner("6.4 HAND-CHECK ON 20 EVENTS"); ev=H20[:]; random.Random(1).shuffle(ev)
    print("events sorted by account (for hand-checking):"); [print("  ",e) for e in sorted(H20)]
    fn,_=naive(ev); fk,_,_=keyed(ev); print("hand-derived flagged accounts (written before run):",sorted(HAND_EXPECTED))
    print("NAIVE :",sorted(fn),"| KEYED:",sorted(fk),"| both equal hand answer:",set(fn)==set(fk)==HAND_EXPECTED); show(fk)
    res["hand20"]={"naive":sorted(fn),"keyed":sorted(fk),"hand":sorted(HAND_EXPECTED),"equal":set(fn)==set(fk)==HAND_EXPECTED}
    ev5=gen(5000,0); a,_=naive(ev5); b_,_,_=keyed(ev5); print("5,000 random events: naive == keyed (accounts AND events):",a==b_,"| flagged accounts:",len(a)); res["rand5000_agree"]=a==b_
    shot("6.4 - 20-event block")
    banner("6.5 GROWTH (each run in its own process; peak memory = max RSS incl. the generated list)")
    nv=[]
    for n in (2000,5000,10000):
        r=[run_child("naive",n) for _ in range(3)]; ts=[x["s"] for x in r]; nv.append({"n":n,"runs":ts,"comparisons":n*n}); print(f"NAIVE {n:>6} events: {n*n:>14,} comparisons | {fmt(ts)}")
    tpc=msd(nv[-1]["runs"])[0]/(10000**2)
    ex={}
    for n in (100_000,1_000_000,10_000_000):
        ex[n]=tpc*n*n; print(f"NAIVE {n:>10,} events: {n*n:>20,} comparisons | EXTRAPOLATED (n^2) {ex[n]:,.0f} s = {ex[n]/3600:,.1f} h  (not measured)")
    kv=[]
    for n,runs in ((10_000,3),(100_000,3),(1_000_000,3),(10_000_000,1)):
        r=[run_child("keyed",n) for _ in range(runs)]
        if r[0].get("failed"): print(f"KEYED {n:>10,}: FAILED (likely out of memory) rc={r[0]['returncode']}"); kv.append({"n":n,"failed":True}); continue
        ts=[x["s"] for x in r]; print(f"KEYED {n:>10,} events: {r[0]['proc']:>12,} records processed | {fmt(ts)} ({runs} run{'s' if runs>1 else ''}) | peak window state {r[0]['peak']} | max RSS {r[0]['rss_mb']:.0f} MB | flagged accounts {r[0]['flagged']}")
        kv.append({"n":n,"runs":ts,"proc":r[0]["proc"],"peak_state":r[0]["peak"],"rss_mb":r[0]["rss_mb"],"flagged":r[0]["flagged"]})
    banner("6.5 SKEW: 1,000,000 events, 30% from ONE account")
    import numpy as np
    for sk in (0,0.3):
        a,_,_=gen_arrays(1_000_000,sk); ld=np.bincount(a%8,minlength=8); print(f"skew {sk}: events per reducer (8 reducers by account%8): {ld.tolist()} | max/mean = {ld.max()/ld.mean():.2f}")
    r=[run_child("keyed",1_000_000,0.3) for _ in range(3)]; ts=[x["s"] for x in r]
    print(f"KEYED skewed 1M: {fmt(ts)} | peak window state (hot account) {r[0]['peak']} entries | max RSS {r[0]['rss_mb']:.0f} MB")
    res.update({"naive":nv,"naive_extrapolated_s":ex,"keyed":kv,"skew":{"time":ts,"peak":r[0]["peak"],"rss":r[0]["rss_mb"]}}); save("task6",res)
    shot("6.5 - growth lines and skew block")
