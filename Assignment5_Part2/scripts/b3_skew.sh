source ~/csa15_a5/Assignment5_Part2/scripts/lib.sh
echo "### PREDICTION made before running the jobs - $(date)" | tee $R/skew_prediction.txt
python3 $SRC/predict_skew.py 4 $D/skew_uniform_500mb.csv $D/skew_hot_500mb.csv | tee -a $R/skew_prediction.txt
for k in uniform hot; do
  hdfs dfs -test -e /transit/raw/skew_${k}_500mb.csv || hdfs dfs -put -f $D/skew_${k}_500mb.csv /transit/raw/
  echo "[run] skew_$k (4 reducers, no combiner)"
  runq1 skew_$k /transit/raw/skew_${k}_500mb.csv /transit/out/skew_$k 4 no
  J=$(jobid $R/skew_$k.log)
  for i in 1 2 3 4 5 6; do python3 $SRC/reducer_stats.py $J > $R/skew_${k}_reducers.txt 2>/dev/null && break; sleep 10; done
  echo "--- $k: $J, total elapsed $(ctr $R/skew_$k.log ELAPSED_SECONDS) s"; cat $R/skew_${k}_reducers.txt
  hdfs dfs -du /transit/out/skew_$k | grep part
done
