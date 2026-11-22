source ~/csa15_a5/Assignment5_Part2/scripts/lib.sh
awk 'NR==1000{print "2026-11-01 08:00:00,S001,G1,CFAIL,ENTRY,0"} {print}' $D/ds_500mb.csv > $D/poison_500mb.csv
hdfs dfs -put -f $D/poison_500mb.csv /transit/raw/poison_500mb.csv
for mode in transient permanent; do
  echo; echo "=== failure mode: $mode (poison record CFAIL in the first split, mapreduce.map.maxattempts=4)"
  XS=(-cmdenv FAIL_MODE=$mode)
  runq1 fail_$mode /transit/raw/poison_500mb.csv /transit/out/fail_$mode 2 yes -D mapreduce.map.maxattempts=4
  XS=()
  L=$R/fail_$mode.log
  grep -E "Status : FAILED|Job .*(completed successfully|failed)|Failed map tasks|Launched map tasks|Killed map tasks|failedMaps" $L | sed 's/^[ \t]*//' | cut -c1-190
  J=$(jobid $L); APP=${J/job_/application_}; sleep 10
  echo "-- from the container logs:"; yarn logs -applicationId $APP 2>/dev/null | grep "FAULT INJECTED" | cut -c1-160 | head -6
done
if hdfs dfs -test -e /transit/out/comb_yes; then
  echo "--- transient run vs clean run (expect 1 changed line: the poison record is a valid ENTRY at S001 2026-11-01 08)"
  diff <(hdfs dfs -cat /transit/out/comb_yes/part-* | LC_ALL=C sort) <(hdfs dfs -cat /transit/out/fail_transient/part-* | LC_ALL=C sort)
fi
