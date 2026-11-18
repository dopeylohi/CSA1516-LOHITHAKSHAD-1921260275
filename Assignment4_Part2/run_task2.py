import random, time, pickle, tracemalloc
from common import *
W=60
def mk(minutes,per,seed):
    rng=random.Random(seed); ev=[]; step=W//per
    for m in range(minutes):
        for j in range(per): ev.append((f"e{len(ev)}",f"S{rng.randint(1,20)}",round(rng.uniform(20,80),1),m*W+j*step))
    return ev                                   # (event_id,sensor,speed,event_time_s)
def batch(ev):
    seen=set(); w={}
    for i,s,v,t in ev:
        if i in seen: continue
        seen.add(i); a=w.setdefault(t//W*W,[0.0,0]); a[0]+=v; a[1]+=1
    return {k:(round(a[0]/a[1],4),a[1]) for k,a in sorted(w.items())}
def new_state(): return {"wins":{},"ids":{},"nids":0,"maxet":-1,"out":{},"late":[],"dups":[],"peak":0}
def close(S,wm,final=False):
    lim=S["maxet"]-wm
    for k in sorted(S["wins"]):
        if final or k+W<=lim:
            a=S["wins"].pop(k); S["out"][k]=(round(a[0]/a[1],4),a[1],S["maxet"],final)
            S["nids"]-=len(S["ids"].pop(k,()))
def stream(ev,wm,dedupe=True,S=None,final=True):
    S=S if S is not None else new_state()
    for i,s,v,t in ev:
        k=t//W*W
        if k+W<=S["maxet"]-wm: S["late"].append((i,t,S["maxet"])); continue   # window already closed
        if dedupe:
            seen=S["ids"].setdefault(k,set())
            if i in seen: S["dups"].append(i); continue
            seen.add(i); S["nids"]+=1
        a=S["wins"].setdefault(k,[0.0,0]); a[0]+=v; a[1]+=1
        if t>S["maxet"]: S["maxet"]=t; close(S,wm)
        S["peak"]=max(S["peak"],len(S["wins"])+S["nids"])
    if final: close(S,wm,True)
    return S
def result(S): return {k:(v[0],v[1]) for k,v in sorted(S["out"].items())}
def latency(S):
    l=[v[2]-(k+W) for k,v in S["out"].items() if not v[3]]; return sum(l)/len(l) if l else 0
def diff(a,b): return sorted(k for k in set(a)|set(b) if a.get(k)!=b.get(k))
def mkbig(minutes=600,per=60,late=.03,dup=.02,seed=7):
    rng=random.Random(seed); arr=[]
    for i,e in enumerate(mk(minutes,per,seed)):
        d=rng.uniform(5,100) if rng.random()<late else 0
        arr.append((e[3]+d,i,e))
        if rng.random()<dup: arr.append((e[3]+d+rng.uniform(0,5),i+.5,e))
    arr.sort(key=lambda x:(x[0],x[1])); return [x[2] for x in arr]

if __name__=="__main__":
    banner("TASK 2 - ENVIRONMENT"); res={"env":env()}
    banner("2.1 NORMAL CASE (ordered, clean, 5 windows x 20 events; watermark 10 s, window 60 s)")
    ev=mk(5,20,1); b=batch(ev); S=stream(ev,10); s=result(S)
    print("window_start | BATCH (avg,n) | STREAM (avg,n) | same")
    for k in b: print(f"{k:>12} | {b[k]} | {s.get(k)} | {b[k]==s.get(k)}")
    print("StreamResult = BatchResult" if not diff(s,b) else "StreamResult != BatchResult"); res["normal"]={"batch":b,"stream":s,"equal":not diff(s,b)}
    shot("2.1 - the side-by-side table")
    banner("2.2 BREAK THE STREAM (late + out-of-order + duplicate events)")
    ev2=mk(5,20,1); late=ev2.pop(3)                                  # event_time 9 s (window 0)
    j=next(i for i,e in enumerate(ev2) if e[3]>=95); ev2.insert(j+1,late)   # arrives after the 96 s event
    j=next(i for i,e in enumerate(ev2) if e[3]==141); ev2[j],ev2[j+1]=ev2[j+1],ev2[j]   # out of order but inside watermark
    ev2.insert(51,ev2[50])                                           # exact duplicate
    b2=batch(ev2); S=stream(ev2,10,True); s2=result(S); d=diff(s2,b2)
    print("BATCH :",b2); print("STREAM:",s2)
    print("StreamResult != BatchResult" if d else "StreamResult = BatchResult","| windows that differ:",d)
    fl=S["late"][0]; print(f"FIRST responsible event: id={fl[0]} event_time={fl[1]}s arrived when max event_time was {fl[2]}s -> {fl[2]-fl[1]}s late; watermark delay is 10 s, its window [0,60) was already closed (watermark={fl[2]-10}s). Setting: WATERMARK.")
    print("duplicates removed by de-dup (window-scoped state):",len(S["dups"]),"| late events dropped:",len(S["late"]))
    fixed=next(w for w in range(0,300) if not diff(result(stream(ev2,w,True)),b2))
    Sf=stream(ev2,fixed,True); S10=stream(ev2,10,True)
    print(f"FIX: watermark {fixed} s -> StreamResult = BatchResult: {not diff(result(Sf),b2)}")
    print(f"COST: mean result delay {latency(S10):.1f}s -> {latency(Sf):.1f}s (event-time clock); peak state items {S10['peak']} -> {Sf['peak']}")
    Sn=stream(ev2,fixed,False); dn=diff(result(Sn),b2)
    print("Second setting: de-dup OFF (watermark",fixed,") -> windows differ:",dn,"=> duplicates inflate counts; DE-DUP setting responsible")
    res["break"]={"differ":d,"first_event":fl,"fixed_watermark":fixed,"lat_before":latency(S10),"lat_after":latency(Sf),"peak_before":S10["peak"],"peak_after":Sf["peak"],"nodedup_differ":dn}
    shot("2.2 - mismatch line, responsible event, fix and cost")
    banner("2.3 ENGINEERING COMPARISON (36,000 events, 3% late 5-100 s, 2% duplicates)")
    big=mkbig(); N=len(big); bb=batch(big); maxet=max(e[3] for e in big); res["n_events"]=N; comp={}
    _,ts=timeit(lambda:batch(big)); tracemalloc.start(); batch(big); bm=tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
    bl=sum(maxet-(k+W) for k in bb)/len(bb)
    print(f"BATCH : throughput {N/msd(ts)[0]:,.0f} ev/s ({fmt(ts)}) | result delay {bl:.0f}s after data ends (needs whole file) | memory peak {bm/1e6:.1f} MB (holds all {N} events) | correct by definition")
    comp["batch"]={"time":ts,"lat":bl,"mem_MB":bm/1e6}
    for wm in (2,10,130):
        _,ts=timeit(lambda:stream(big,wm)); S=stream(big,wm); r=result(S)
        tracemalloc.start(); stream(big,wm); sm=tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
        wrong=len(diff(r,bb))
        print(f"STREAM wm={wm:>3}s: throughput {N/msd(ts)[0]:,.0f} ev/s ({fmt(ts)}) | delay {latency(S):.1f}s | peak state {S['peak']} items, mem {sm/1e6:.2f} MB | wrong windows {wrong}/{len(bb)} | late dropped {len(S['late'])} | dups removed {len(S['dups'])}")
        comp[f"stream_wm{wm}"]={"time":ts,"lat":latency(S),"peak":S["peak"],"mem_MB":sm/1e6,"wrong":wrong,"late":len(S["late"]),"dups":len(S["dups"])}
    H=N//2; full=stream(big,130); S1=stream(big[:H],130,final=False); blob=pickle.dumps(S1)
    S2=stream(big[H:],130,S=pickle.loads(blob)); cp=result(S2)==result(full)
    SL=stream(big[H:],130); merged=dict(result(S1)); merged.update(result(SL)); lost=len(diff(merged,result(full)))
    b_again=batch(big)==bb
    print(f"RESTART at event {H}: with checkpoint -> identical to uninterrupted run: {cp} | stateless restart -> {lost} windows differ | batch rerun identical: {b_again}")
    comp["restart"]={"checkpoint_identical":cp,"stateless_wrong_windows":lost,"batch_rerun_identical":b_again}
    res["compare"]=comp; shot("2.3 - BATCH/STREAM lines and RESTART line")
    banner("2.4 TWO-SECOND REQUIREMENT: watermark sweep on the same data")
    print("watermark_s | mean result delay s | wrong windows | late events dropped (% of events) | peak state")
    sw=[]
    for wm in (0,1,2,5,10,30,60,100,130):
        S=stream(big,wm); wrong=len(diff(result(S),bb)); pc=100*len(S["late"])/N
        print(f"{wm:>11} | {latency(S):>19.1f} | {wrong:>13} | {len(S['late']):>6} ({pc:.2f}%) | {S['peak']}")
        sw.append({"wm":wm,"lat":latency(S),"wrong":wrong,"late":len(S["late"]),"pct":pc,"peak":S["peak"]})
    res["sweep"]=sw; save("task2",res); shot("2.4 - the sweep table")
