source ~/csa15_a5/Assignment5_Part2/scripts/lib.sh
echo $HDR > $R/scaling.csv
for s in 100 500 1000 2000; do
  hdfs dfs -test -e /transit/raw/ds_${s}mb.csv || hdfs dfs -put -f $D/ds_${s}mb.csv /transit/raw/ds_${s}mb.csv
  for r in 1 2 4; do
    echo "[run] ${s} MB, reducers=$r"
    runq1 scale_${s}_r$r /transit/raw/ds_${s}mb.csv /transit/out/scale_${s}_r$r $r yes
    csvrow $R/scale_${s}_r$r.log "${s}MB_r$r" >> $R/scaling.csv
    hdfs dfs -rm -r -f -skipTrash /transit/out/scale_${s}_r$r >/dev/null
  done
done
column -s, -t $R/scaling.csv
