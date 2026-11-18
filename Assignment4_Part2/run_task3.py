import sqlite3, hmac, hashlib, json, random, time, os, datetime, shutil
from collections import defaultdict, Counter
from common import *
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
rng=random.Random(42)
FN="Aarav Bala Charan Divya Esha Farhan Gokul Hari Indu Jaya Kavin Lata".split()
LN="Kumar Raj Nair Iyer Reddy Das Menon Pillai Gupta Shah Rao Joshi".split()
SCH=["PMJAY","PMAY","MGNREGA","PMKISAN","NSAP"]
def gen(n=2000):
    d0=datetime.date(1950,1,1); P=[]
    for i in range(n):
        P.append({"Name":f"{rng.choice(FN)} {rng.choice(LN)} {i}","ID_Number":f"B{100000+i}","PIN_Code":str(600001+rng.randint(0,29)),
          "Date_of_Birth":(d0+datetime.timedelta(rng.randint(0,20000))).isoformat(),"Gender":rng.choice("MF"),"Scheme":rng.choice(SCH),"Amount":rng.randint(2000,50000)})
    aux=[{k:p[k] for k in ("Name","PIN_Code","Date_of_Birth","Gender")} for p in rng.sample(P,int(.6*n))]
    return P,aux
class Audit:
    def __init__(s,path): s.path=path; s.prev="0"*64; s.i=0; open(path,"w").close()
    def log(s,user,role,action,rows):
        e={"i":s.i,"ts":datetime.datetime.now().isoformat(timespec="seconds"),"user":user,"role":role,"action":action,"rows":rows,"prev":s.prev}
        e["hash"]=hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest()
        open(s.path,"a").write(json.dumps(e)+"\n"); s.prev=e["hash"]; s.i+=1; return e
def verify_chain(path):
    prev="0"*64
    for ln in open(path):
        e=json.loads(ln); h=e.pop("hash")
        if e["prev"]!=prev or hashlib.sha256(json.dumps(e,sort_keys=True).encode()).hexdigest()!=h: return e["i"]
        prev=h
    return None

banner("TASK 3 - ENVIRONMENT"); res={"env":env()}
P,aux=gen(); print("synthetic beneficiaries:",len(P),"| auxiliary public records:",len(aux))
DB=f"{DATA}/t3.db"
if os.path.exists(DB): os.remove(DB)
con=sqlite3.connect(DB)
con.execute("CREATE TABLE beneficiary(Name,ID_Number,PIN_Code,Date_of_Birth,Gender,Scheme,Amount)")
con.executemany("INSERT INTO beneficiary VALUES(?,?,?,?,?,?,?)",[tuple(p.values()) for p in P])
con.execute("CREATE VIEW v_analyst AS SELECT * FROM beneficiary")
con.execute("CREATE VIEW v_researcher AS SELECT PIN_Code,Date_of_Birth,Gender,Scheme,Amount FROM beneficiary"); con.commit()
AUD=f"{RES}/audit_log.jsonl"; audit=Audit(AUD)
PERM={"fraud_analyst":{"v_analyst","v_researcher"},"researcher":{"v_researcher"}}
def access(role,user,view,n=3):
    if view not in PERM[role]:
        e=audit.log(user,role,f"DENIED SELECT FROM {view}",0); return None,e
    rows=con.execute(f"SELECT * FROM {view}").fetchall(); e=audit.log(user,role,f"SELECT FROM {view}",len(rows)); return rows[:n],e
banner("STAGE A - ROLES + AUDIT")
for role,user,view in (("fraud_analyst","analyst01","v_analyst"),("researcher","res01","v_researcher"),("researcher","res01","v_analyst")):
    rows,e=access(role,user,view); print(f"\n{role} ({user}) asks {view}:"); print(" columns seen:",[c[0] for c in con.execute(f'SELECT * FROM {view}').description])
    print(" first 2 rows:",rows[:2] if rows else "ACCESS DENIED"); print(" audit entry:",{k:e[k] for k in ("i","user","role","action","rows")},"hash",e["hash"][:12]+"...")
print("\naudit chain verifies:",verify_chain(AUD) is None); res["A"]={"chain_ok":verify_chain(AUD) is None}
shot("Stage A - role outputs and audit entries")
banner("STAGE B - LINKAGE ATTACK (release = drop Name and ID_Number)")
rel=con.execute("SELECT * FROM v_researcher").fetchall()
cnt=Counter((r[0],r[1],r[2]) for r in rel); uniq=sum(1 for v in cnt.values() if v==1); cov=len(aux)/len(P); predicted=round(uniq*cov)
pred("3B",f"{uniq} released records have a unique (PIN, DOB, Gender); auxiliary covers {cov:.0%} of people, so I expect about {predicted} re-identifications.")
truth={p["Name"]:(p["Scheme"],p["Amount"]) for p in P}
hits=[]
for a in aux:
    k=(a["PIN_Code"],a["Date_of_Birth"],a["Gender"])
    if cnt.get(k)==1:
        r=next(x for x in rel if (x[0],x[1],x[2])==k); hits.append((a["Name"],r[3],r[4]))
correct=sum(1 for n,s,am in hits if truth[n]==(s,am))
print(f"ACTUAL re-identified: {len(hits)} (predicted {predicted}); correct links {correct}; sample:",hits[:3]); res["B"]={"unique":uniq,"predicted":predicted,"actual":len(hits),"correct":correct}
shot("Stage B - prediction line and attack result")
banner("STAGE C - GENERALISATION LATTICE (target k >= 5, assumed)")
def glv(v,lv): return {"exact":v,"month":v[:7],"year":v[:4],"5y":f"{int(v[:4])//5*5}s","10y":f"{int(v[:4])//10*10}s"}[lv]
rows=[(p["PIN_Code"],p["Date_of_Birth"],p["Gender"],p["Amount"]) for p in P]
def err(tk,gk):
    T=defaultdict(list); G=defaultdict(list); rep={}
    for r in rows: T[tk(r)].append(r[3]); G[gk(r)].append(r[3]); rep[tk(r)]=gk(r)
    ov=sum(r[3] for r in rows)/len(rows)
    e=[abs(sum(v)/len(v)-sum(G[rep[t]])/len(G[rep[t]])) for t,v in T.items()]
    return 100*sum(e)/len(e)/ov
lat=[]
print("PIN digits | DOB level | k | records still re-identifiable | utility loss % (avg-amount by PIN, by birth year)")
for pd in (6,5,4,3):
    for dl in ("exact","month","year","5y","10y"):
        key=lambda pin,dob,g:(pin[:pd],glv(dob,dl),g)
        grp=Counter(key(*r[:3]) for r in rows); k=min(grp.values())
        risk=sum(1 for a in aux if grp.get(key(a["PIN_Code"],a["Date_of_Birth"],a["Gender"]))==1)
        e1=err(lambda r:r[0],lambda r:r[0][:pd]); e2=err(lambda r:r[1][:4],lambda r:glv(r[1],dl if dl in("5y","10y") else "year"))
        loss=(e1+e2)/2; lat.append({"pin_digits":pd,"dob":dl,"k":k,"risk":risk,"e_pin":e1,"e_year":e2,"loss":loss})
        print(f"{pd:>10} | {dl:>9} | {k:>3} | {risk:>6} | {loss:5.2f} ({e1:.2f}, {e2:.2f})")
ok=[x for x in lat if x["k"]>=5]; ch=min(ok,key=lambda x:x["loss"]) if ok else None
print("CHOSEN (smallest utility loss with k>=5):",ch); res["C"]={"lattice":lat,"chosen":ch}
shot("Stage C - the lattice table and CHOSEN line")
banner("STAGE D - ENCRYPTION OVERHEAD + INTEGRITY")
key=AESGCM.generate_key(256); aes=AESGCM(key); NB=200_000
amts=[rng.randint(2000,50000) for _ in range(NB)]; sch=[rng.choice(SCH) for _ in range(NB)]
def enc(i,a): n=os.urandom(12); return n+aes.encrypt(n,str(a).encode(),b"row%d"%i)
t=time.perf_counter(); encs=[enc(i,a) for i,a in enumerate(amts)]; t_enc=time.perf_counter()-t
def plain():
    tot=defaultdict(int)
    for s,a in zip(sch,amts): tot[s]+=a
    return dict(tot)
def encrypted():
    tot=defaultdict(int)
    for i,(s,c) in enumerate(zip(sch,encs)): tot[s]+=int(aes.decrypt(c[:12],c[12:],b"row%d"%i))
    return dict(tot)
o1,t1=timeit(plain); o2,t2=timeit(encrypted)
print(f"pipeline on {NB} records (avg-by-scheme input): plain {fmt(t1)} | AES-256-GCM encrypted Amount {fmt(t2)} | overhead x{msd(t2)[0]/msd(t1)[0]:.1f} | same result: {o1==o2}")
print(f"one-time encryption of {NB} fields: {t_enc:.2f}s | stored size per field: {len(encs[0])} bytes vs {len(str(amts[0]))} plain")
res["D_overhead"]={"plain":t1,"enc":t2,"encrypt_once_s":t_enc,"same":o1==o2}
HK=os.urandom(32)
def mac(rec): return hmac.new(HK,json.dumps(rec,sort_keys=True).encode(),hashlib.sha256).hexdigest()
store=[]
for i,p in enumerate(P):
    r=dict(p); n=os.urandom(12); r["ID_Number"]=(n+aes.encrypt(n,p["ID_Number"].encode(),b"row%d"%i)).hex(); r["mac"]=mac(r); store.append(r)
SP=f"{DATA}/protected.jsonl"; open(SP,"w").write("\n".join(json.dumps(r) for r in store)+"\n")
sha=hashlib.sha256(open(SP,"rb").read()).hexdigest()
def verify(path):
    L=[json.loads(x) for x in open(path)]; bad=[]
    for i,r in enumerate(L):
        m=r.pop("mac")
        if not hmac.compare_digest(m,mac(r)): bad.append(i)
    return {"bad_record_macs":bad,"count_ok":len(L)==len(P),"file_sha_ok":hashlib.sha256(open(path,"rb").read()).hexdigest()==sha}
print("\nuntouched file:",verify(SP))
L=[json.loads(x) for x in open(SP)]; L[100]["Amount"]+=1
open(f"{DATA}/t_alter.jsonl","w").write("\n".join(json.dumps(r) for r in L)+"\n"); a=verify(f"{DATA}/t_alter.jsonl"); print("ALTER record 100 Amount by +1 ->",a)
L=[json.loads(x) for x in open(SP)]; del L[500]
open(f"{DATA}/t_del.jsonl","w").write("\n".join(json.dumps(r) for r in L)+"\n"); d=verify(f"{DATA}/t_del.jsonl"); print("DELETE record 500 ->",d,"(record MACs all valid; only count/file hash notice)")
shutil.copy(AUD,f"{DATA}/audit_t.jsonl"); ls=open(f"{DATA}/audit_t.jsonl").read().split("\n"); e=json.loads(ls[1]); e["rows"]=999999; ls[1]=json.dumps(e)
open(f"{DATA}/audit_t.jsonl","w").write("\n".join(ls)); v=verify_chain(f"{DATA}/audit_t.jsonl"); print("EDIT audit entry 1 -> hash chain breaks at entry:",v)
res["D_integrity"]={"alter":a,"delete":d,"audit_break_at":v}; save("task3",res)
shot("Stage D - overhead line and the three tamper results")
