source ~/csa15_a5/Assignment5_Part2/scripts/lib.sh
L=$R/b1_hdfs_commands.log; F=/transit/raw/gate_log_500mb.csv
python3 - $D <<'PY'
import sqlite3, csv, sys
d = sys.argv[1]; db = sqlite3.connect(d + "/transit.db")
db.execute("drop table if exists fare"); db.execute("create table fare(from_zone int, to_zone int, fare real)")
rows = [(a, b, 10 + 5*abs(a-b)) for a in range(1, 5) for b in range(1, 5)]   # assumed fare table
db.executemany("insert into fare values(?,?,?)", rows); db.commit()
csv.writer(open(d + "/fare_table.csv", "w", newline="")).writerows(rows)
print("relational table 'fare' created:", db.execute("select count(*) from fare").fetchone()[0], "rows")
PY
{
echo "### daemons"; jps
echo "### create directory structure"; hdfs dfs -mkdir -p /transit/raw /transit/ref /transit/out /transit/test; hdfs dfs -ls /transit
echo "### upload generated log (500 MB)"; hdfs dfs -put -f $D/ds_500mb.csv $F
echo "### list files"; hdfs dfs -ls -h /transit/raw
echo "### space usage"; hdfs dfs -du -h /transit/raw; hdfs dfs -df -h /
echo "### file attributes"; hdfs dfs -stat "replication=%r blocksize=%o bytes=%b" $F
echo "### fsck, replication 1"; hdfs fsck $F -files -blocks -locations | tee $R/fsck_rep1.txt
echo "### change replication to 2"; hdfs dfs -setrep 2 $F; hdfs dfs -stat "replication=%r" $F
hdfs fsck $F -files -blocks -locations | tee $R/fsck_rep2.txt
echo "### restore replication to 1"; hdfs dfs -setrep 1 $F
echo "### B1.3 data IN: relational table -> HDFS"; hdfs dfs -put -f $D/fare_table.csv /transit/ref/; hdfs dfs -cat /transit/ref/fare_table.csv | head -5
} > $L 2>&1
echo "===== B1 KEY LINES ====="
sed -n '/### list files/,/### fsck, replication 1/p' $L | grep -v '^###.*fsck'
K="blk_|Total blocks|Default replication|Average block replication|Under-replicated|Missing replicas|Number of data-nodes"
echo "--- fsck, replication 1"; grep -E "$K" $R/fsck_rep1.txt | cut -c1-170
echo "--- fsck, after setrep 2"; grep -E "$K" $R/fsck_rep2.txt | cut -c1-170
