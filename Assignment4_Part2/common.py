import json, os, time, platform, statistics as st, datetime
BASE=os.path.dirname(os.path.abspath(__file__))
RES=f"{BASE}/results"; DATA=f"{BASE}/data"; LOGS=f"{BASE}/logs"
for _d in (RES,DATA,LOGS): os.makedirs(_d,exist_ok=True)
def save(name,obj):
    with open(f"{RES}/{name}.json","w") as f: json.dump(obj,f,indent=1,default=str)
def env():
    e={"python":platform.python_version(),"os":platform.platform(),"cpus":os.cpu_count()}
    try: e["ram_GB_visible"]=round(int(open("/proc/meminfo").readline().split()[1])/1048576,1)
    except Exception: pass
    for m in ("numpy","pyarrow","cryptography"):
        try: e[m]=__import__(m).__version__
        except Exception: pass
    print("ENV:",e); return e
def msd(xs): return (st.mean(xs), st.stdev(xs) if len(xs)>1 else 0.0)
def fmt(xs,u="s"):
    m,s=msd(xs); return f"{m:.3f}±{s:.3f}{u}"
def banner(t): print(f"\n===== {t} =====")
def shot(t): print(f"\n>>>>>> SCREENSHOT NOW: {t} <<<<<<")
def pred(task,text):
    ts=datetime.datetime.now().strftime("%H:%M:%S")
    with open(f"{RES}/predictions.txt","a") as f: f.write(f"[{ts}] {task}: {text}\n")
    print(f"PREDICTION (recorded {ts}, BEFORE the run) {task}: {text}")
def timeit(fn,runs=3):
    ts=[];out=None
    for _ in range(runs):
        t=time.perf_counter(); out=fn(); ts.append(time.perf_counter()-t)
    return out,ts
