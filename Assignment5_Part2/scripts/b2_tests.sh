source ~/csa15_a5/Assignment5_Part2/scripts/lib.sh
T=$A/tests; hdfs dfs -mkdir -p /transit/test
rt(){ n=$1; shift
  hdfs dfs -rm -r -f -skipTrash /transit/test/$n >/dev/null 2>&1; hdfs dfs -mkdir -p /transit/test/$n; hdfs dfs -put -f "$@" /transit/test/$n/
  runq1 test_$n /transit/test/$n /transit/test_out/$n 1 yes
  hdfs dfs -cat /transit/test_out/$n/part-* | LC_ALL=C sort > $R/actual_$n.txt
  echo; echo "=== TEST $n (input: $*)"
  echo "-- expected:"; cat $T/expected_$n.txt; echo "-- actual (Hadoop):"; cat $R/actual_$n.txt
  cmp -s <(LC_ALL=C sort $T/expected_$n.txt) $R/actual_$n.txt && echo "RESULT: PASS" || echo "RESULT: FAIL"
  grep -E "MalformedRecords|ExitTapsSkipped|Map input records|Map output records|Combine input records|Combine output records|Launched map tasks" $R/test_$n.log | sed 's/^[ \t]*//'
}
cd $T; rt sample sample_part1.csv sample_part2.csv; rt malformed malformed.csv; rt exit_only exit_only.csv; rt empty empty.csv
echo; echo "=== Q1 and Q2 on a 20 MB synthetic file vs an independent Python script (no Hadoop)"
hdfs dfs -put -f $D/topn_20mb.csv /transit/raw/topn_20mb.csv
runq1 q1_20mb /transit/raw/topn_20mb.csv /transit/out/q1_20mb 2 yes
hdfs dfs -cat /transit/out/q1_20mb/part-* | LC_ALL=C sort > $R/q1_20mb_hadoop.txt
python3 $SRC/verify.py $D/topn_20mb.csv q1 | LC_ALL=C sort > $R/q1_20mb_python.txt
cmp -s $R/q1_20mb_hadoop.txt $R/q1_20mb_python.txt && echo "Q1: Hadoop output MATCHES independent script ($(wc -l < $R/q1_20mb_python.txt) keys)" || echo "Q1: MISMATCH"
runq2 /transit/raw/topn_20mb.csv /transit/out/q2_20mb 2
hdfs dfs -cat /transit/out/q2_20mb-j2/part-* | LC_ALL=C sort > $R/q2_20mb_hadoop.txt
python3 $SRC/verify.py $D/topn_20mb.csv q2 | LC_ALL=C sort > $R/q2_20mb_python.txt
cmp -s $R/q2_20mb_hadoop.txt $R/q2_20mb_python.txt && echo "Q2: Hadoop top-5 MATCHES independent script" || echo "Q2: MISMATCH"
echo "Q2 top-5 per day (Hadoop two-job chain):"; cat $R/q2_20mb_hadoop.txt
echo "--- B1.3 data OUT: job output -> local file -> relational table"
hdfs dfs -getmerge /transit/out/q2_20mb-j2 $R/q2_top5_exported.tsv
python3 - $D $R <<'PY'
import sqlite3, csv, sys
db = sqlite3.connect(sys.argv[1] + "/transit.db")
db.execute("drop table if exists top_stations"); db.execute("create table top_stations(day text, station text, entries int)")
db.executemany("insert into top_stations values(?,?,?)", csv.reader(open(sys.argv[2] + "/q2_top5_exported.tsv"), delimiter="\t")); db.commit()
print("rows loaded into table top_stations:", db.execute("select count(*) from top_stations").fetchone()[0])
for r in db.execute("select * from top_stations order by day, entries desc limit 5"): print(r)
PY
