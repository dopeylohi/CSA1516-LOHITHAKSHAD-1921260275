import os, re, shutil, time, sqlite3
import numpy as np, pyarrow as pa, pyarrow.csv as pcsv, pyarrow.parquet as pq, pyarrow.compute as pc
from common import *
N=5_000_000; D=f"{DATA}/t5"; shutil.rmtree(D,ignore_errors=True); os.makedirs(D)
CSV,PQ,DB=f"{D}/events.csv",f"{D}/events.parquet",f"{D}/events.db"
SENSOR,DAY,D0,D1=123,5,3,9
def table(n,seed,lo,hi):
    r=np.random.default_rng(seed); ts=np.sort(r.integers(lo,hi,n)); sid=r.integers(1,1001,n)
    return pa.table({"sensor_id":sid,"segment":sid%50+1,"speed":np.round(r.normal(45,12,n).clip(5,120),1),"ts":ts,"day":ts//86400})
banner("TASK 5 - ENVIRONMENT"); res={"env":env()}
T=table(N,5,0,14*86400); build={}
t=time.perf_counter(); pcsv.write_csv(T,CSV); build["csv_s"]=time.perf_counter()-t
t=time.perf_counter(); pq.write_table(T,PQ,row_group_size=250_000,compression="snappy"); build["parquet_s"]=time.perf_counter()-t
t=time.perf_counter(); con=sqlite3.connect(DB); con.execute("PRAGMA journal_mode=OFF"); con.execute("PRAGMA synchronous=OFF")
con.execute("CREATE TABLE events(sensor_id INT,segment INT,speed REAL,ts INT,day INT)")
for b in T.to_batches(200_000): con.executemany("INSERT INTO events VALUES(?,?,?,?,?)",zip(*[c.to_pylist() for c in b.columns]))
con.commit(); build["sqlite_load_s"]=time.perf_counter()-t
t=time.perf_counter(); con.execute("CREATE INDEX idx_sd ON events(sensor_id,day)"); con.commit(); build["idx_sd_s"]=time.perf_counter()-t; con.close()
sizes={"csv":os.path.getsize(CSV),"parquet":os.path.getsize(PQ),"sqlite_with_idx_sd":os.path.getsize(DB)}
print("events:",N,"| build seconds:",{k:round(v,1) for k,v in build.items()}); print("sizes MB:",{k:round(v/1e6,1) for k,v in sizes.items()})
CSZ=sizes["csv"]
def csv_q1(lo=SENSOR,hi=SENSOR):
    t=pcsv.read_csv(CSV); m=pc.and_(pc.and_(pc.greater_equal(t["sensor_id"],lo),pc.less_equal(t["sensor_id"],hi)),pc.equal(t["day"],DAY)); return t.filter(m).num_rows,CSZ,"full file scanned"
def csv_q2(cols=("segment","speed","day"),by=True):
    t=pcsv.read_csv(CSV,convert_options=pcsv.ConvertOptions(include_columns=list(cols)))
    t=t.filter(pc.and_(pc.greater_equal(t["day"],D0),pc.less_equal(t["day"],D1)))
    if by: g=t.group_by("segment").aggregate([("speed","mean")]); return round(sum(g["speed_mean"].to_pylist()),2),CSZ,"full file scanned (text cannot skip columns)"
    return round(pc.mean(t["speed"]).as_py(),3),CSZ,"full file scanned (text cannot skip columns)"
def pq_scan(cols,lo,hi):
    pf=pq.ParquetFile(PQ); md=pf.metadata; names=[md.schema.column(j).name for j in range(md.num_columns)]
    di=names.index("day"); ci=[names.index(c) for c in cols]; keep=[]; b=0
    for i in range(md.num_row_groups):
        rg=md.row_group(i); s=rg.column(di).statistics
        if s is not None and s.has_min_max and (s.max<lo or s.min>hi): continue
        keep.append(i); b+=sum(rg.column(j).total_compressed_size for j in ci)
    return pf.read_row_groups(keep,columns=cols),b,f"{len(keep)}/{md.num_row_groups} row groups read"
ALL=["sensor_id","segment","speed","ts","day"]
def pq_q1(lo=SENSOR,hi=SENSOR):
    t,b,n=pq_scan(ALL,DAY,DAY); m=pc.and_(pc.and_(pc.greater_equal(t["sensor_id"],lo),pc.less_equal(t["sensor_id"],hi)),pc.equal(t["day"],DAY)); return t.filter(m).num_rows,b,n
def pq_q2(cols=("segment","speed","day"),by=True):
    t,b,n=pq_scan(list(cols),D0,D1); t=t.filter(pc.and_(pc.greater_equal(t["day"],D0),pc.less_equal(t["day"],D1)))
    if by: g=t.group_by("segment").aggregate([("speed","mean")]); return round(sum(g["speed_mean"].to_pylist()),2),b,n
    return round(pc.mean(t["speed"]).as_py(),3),b,n
def sq(sql,args):
    c=sqlite3.connect(DB); r=c.execute(sql,args).fetchall(); c.close(); return r
Q1S="SELECT * FROM events WHERE sensor_id BETWEEN ? AND ? AND day=?"; Q2S="SELECT segment,AVG(speed) FROM events WHERE day BETWEEN ? AND ? GROUP BY segment"; Q2BS="SELECT AVG(speed) FROM events WHERE day BETWEEN ? AND ?"
def sizes_db():
    try: c=sqlite3.connect(DB); return dict(c.execute("SELECT name,SUM(pgsize) FROM dbstat GROUP BY name").fetchall())
    except Exception: return None
def est(sql,args,matched):
    c=sqlite3.connect(DB); plan=" | ".join(r[3] for r in c.execute("EXPLAIN QUERY PLAN "+sql,args)); c.close(); sz=sizes_db()
    try:
        m=re.search(r"INDEX (\w+)",plan)
        if m and "COVERING" in plan: b=sz[m.group(1)]*matched/N
        elif m: b=(sz[m.group(1)]+sz["events"])*matched/N
        else: b=sz["events"]
        return int(b),plan
    except Exception: return None,plan
NWK=sqlite3.connect(DB).execute("SELECT COUNT(*) FROM events WHERE day BETWEEN ? AND ?",(D0,D1)).fetchone()[0]
def sq_q1(lo=SENSOR,hi=SENSOR):
    r=sq(Q1S,(lo,hi,DAY)); b,p=est(Q1S,(lo,hi,DAY),len(r)); return len(r),b,p
def sq_q2():
    r=sq(Q2S,(D0,D1)); b,p=est(Q2S,(D0,D1),NWK); return round(sum(x[1] for x in r),2),b,p
def sq_q2b():
    r=sq(Q2BS,(D0,D1)); b,p=est(Q2BS,(D0,D1),NWK); return round(r[0][0],3),b,p
rows=[]
def run(store,q,fn,runs=4):
    ts=[];o=None
    for _ in range(runs):
        t=time.perf_counter(); o=fn(); ts.append(time.perf_counter()-t)
    m,s=msd(ts[1:]); row={"store":store,"query":q,"result":o[0],"bytes_scanned":o[1],"note":o[2],"cold_s":ts[0],"warm_mean_s":m,"warm_sd_s":s}; rows.append(row)
    print(f"{store:<14}{q:<5} result={o[0]!s:<12} bytes={o[1]!s:<11} cold {ts[0]:.3f}s | warm {m:.3f}±{s:.3f}s | {o[2]}"); return row
pred("5-base","Q1: CSV slowest (reads whole 5M-row file); Parquet reads only the 2-3 row groups of that day; SQLite index seek fastest (milliseconds). Q2: Parquet fastest (3 of 5 columns, ~half the row groups); CSV slow; SQLite slower than Parquet (row store, scans ~half the table or covering index). Q3: SQLite fast per batch; CSV append fast; Parquet creates one small file per batch (many files).")
banner("Q1 / Q2 (cold = first run; warm = mean of next 3)")
for s,f in (("CSV",csv_q1),("Parquet",pq_q1),("SQLite+idx_sd",sq_q1)): run(s,"Q1",f)
for s,f in (("CSV",csv_q2),("Parquet",pq_q2),("SQLite(no cover)",sq_q2)): run(s,"Q2",f)
print("\nTUNING: SQLite Q2 plan was a table scan; adding covering index idx_day(day,segment,speed)")
c=sqlite3.connect(DB); t=time.perf_counter(); c.execute("CREATE INDEX idx_day ON events(day,segment,speed)"); c.commit(); build["idx_day_s"]=time.perf_counter()-t; c.close()
sizes["sqlite_with_both_idx"]=os.path.getsize(DB); print(" index build",round(build["idx_day_s"],1),"s; db size MB",round(sizes["sqlite_with_both_idx"]/1e6,1))
run("SQLite+idx_day","Q2",sq_q2)
shot("Q1/Q2 block, sizes and tuning line")
pred("5-mod","Q2b (only speed column): CSV unchanged (~same time/bytes); Parquet bytes drop to about 2/3 of Q2 and time falls; SQLite covering index unchanged. Q1b (100 sensors instead of 1): CSV unchanged; Parquet unchanged bytes (same row groups), slightly slower filter; SQLite rows x100 so time grows about 100x vs Q1 and may approach a scan.")
banner("MODIFIED QUERIES")
for s,f in (("CSV",lambda:csv_q2(("speed","day"),False)),("Parquet",lambda:pq_q2(("speed","day"),False)),("SQLite+idx_day",sq_q2b)): run(s,"Q2b",f)
for s,f in (("CSV",lambda:csv_q1(100,199)),("Parquet",lambda:pq_q1(100,199)),("SQLite+idx_sd",lambda:sq_q1(100,199))): run(s,"Q1b",f)
shot("Modified query block")
banner("Q3 WRITE LOAD: 3 runs x 50 batches x 1000 events, durable (fsync / commit per batch)")
BAT=[table(1000,1000+i,14*86400+i*3600,14*86400+i*3600+3600) for i in range(150)]
ROWS=[list(zip(*[c.to_pylist() for c in b.columns])) for b in BAT]; q3={"csv":[],"parquet":[],"sqlite":[]}
for r in range(3):
    sl=slice(r*50,r*50+50)
    t=time.perf_counter()
    with open(CSV,"ab") as f:
        for b in BAT[sl]: pcsv.write_csv(b,f,write_options=pcsv.WriteOptions(include_header=False)); f.flush(); os.fsync(f.fileno())
    q3["csv"].append(50000/(time.perf_counter()-t))
    t=time.perf_counter()
    for i,b in enumerate(BAT[sl]): pq.write_table(b,f"{D}/stream_{r}_{i}.parquet")
    q3["parquet"].append(50000/(time.perf_counter()-t))
    t=time.perf_counter(); c=sqlite3.connect(DB)
    for rows_ in ROWS[sl]: c.executemany("INSERT INTO events VALUES(?,?,?,?,?)",rows_); c.commit()
    c.close(); q3["sqlite"].append(50000/(time.perf_counter()-t))
for k,v in q3.items(): print(f"Q3 {k:<8} {msd(v)[0]:>10,.0f} ± {msd(v)[1]:,.0f} events/s")
nf=len([x for x in os.listdir(D) if x.startswith("stream_")]); print("parquet small files created:",nf,"| total",round(sum(os.path.getsize(f"{D}/{x}") for x in os.listdir(D) if x.startswith("stream_"))/1e6,2),"MB for 150,000 events")
res.update({"build":build,"sizes":sizes,"queries":rows,"q3_events_per_s":q3,"parquet_small_files":nf}); save("task5",res); shot("Q3 block")
