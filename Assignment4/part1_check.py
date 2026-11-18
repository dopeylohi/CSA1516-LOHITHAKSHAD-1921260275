import sqlite3
# ---- TASK 3: sizing ----
st=5000*1440*400/1e9; sat=200
daily=st/3+sat; yr=daily*365*3/1000
usable=12*8*0.7; scan_mb=12*150
print("Station raw GB/day:",st,"| stored:",st/3)
print("Daily stored GB:",daily,"| 1-yr replicated TB:",yr)
print("Nodes storage:",yr/usable,"| Nodes scan:",daily*1000/(scan_mb*7200))
d2=(st/3+2*sat)*365*3/1000
print("Imagery doubled TB:",d2,"| nodes:",d2/usable)
# ---- TASK 4: linkage ----
db=sqlite3.connect(":memory:")
db.executescript("""
create table rel(id int,pin text,dob text,g text,scheme text,amt int);
insert into rel values
(1,'600045','1980-03-12','F','Pension',1500),(2,'600091','1980-07-30','F','Pension',1500),
(3,'600045','1975-11-02','M','Disability',2000),(4,'600102','1975-05-21','M','Disability',2000),
(5,'641002','1990-01-09','F','Scholarship',3000),(6,'641017','1990-09-17','F','Scholarship',3000),
(7,'600045','1968-06-25','M','Pension',1500),(8,'600033','1968-12-01','M','Pension',1500);
create table pub(name text,pin text,dob text,g text);
insert into pub values('Asha','600045','1980-03-12','F'),('Ravi','600045','1968-06-25','M'),
('Meena','641002','1990-01-09','F'),('Kiran','600200','1985-02-02','M');""")
print("\nORIGINAL release joined with public list:")
for r in db.execute("select p.name,r.id,r.scheme,r.amt from rel r join pub p on r.pin=p.pin and r.dob=p.dob and r.g=p.g"):print(r)
print("\nREPAIRED (PIN->3 digits, DOB->year), join result:")
q="select p.name,count(*) c from rel r join pub p on substr(r.pin,1,3)=substr(p.pin,1,3) and substr(r.dob,1,4)=substr(p.dob,1,4) and r.g=p.g group by p.name"
for r in db.execute(q):print(r,"-> matches",r[1],"records (cannot single out)")
print("Smallest group size k:",db.execute("select min(c) from (select count(*) c from rel group by substr(pin,1,3),substr(dob,1,4),g)").fetchone()[0])
print("\nAvg amount per scheme (same before/after repair, since Amount/Scheme untouched):")
for r in db.execute("select scheme,avg(amt) from rel group by scheme"):print(r)
