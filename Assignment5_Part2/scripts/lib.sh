source ~/csa15_a5/env.sh
SRC=$A/src; R=$A/results; XS=()
ctr(){ grep -m1 "$2=" "$1" | sed 's/.*=//'; }
jobid(){ grep -m1 "Running job:" "$1" | awk '{print $NF}'; }
HDR="label,splits,map_tasks,reduce_tasks,map_in,map_out,comb_in,comb_out,shuffle_bytes,reduce_groups,reduce_in,elapsed_s"
csvrow(){ local l=$1; echo "$2,$(grep -m1 'number of splits' $l | sed 's/.*splits://'),$(ctr $l 'Launched map tasks'),$(ctr $l 'Launched reduce tasks'),$(ctr $l 'Map input records'),$(ctr $l 'Map output records'),$(ctr $l 'Combine input records'),$(ctr $l 'Combine output records'),$(ctr $l 'Reduce shuffle bytes'),$(ctr $l 'Reduce input groups'),$(ctr $l 'Reduce input records'),$(ctr $l 'ELAPSED_SECONDS')"; }
runq1(){ # NAME IN OUT REDUCERS yes|no [extra generic -D options]
  local n=$1 i=$2 o=$3 r=$4 c=$5; shift 5; local l=$R/$n.log cb=()
  [ "$c" = yes ] && cb=(-combiner "python3 reducer.py")
  hdfs dfs -rm -r -f -skipTrash $o >/dev/null 2>&1
  SECONDS=0
  hadoop jar $STREAM -D mapreduce.job.name=$n -D mapreduce.job.reduces=$r "$@" \
    -files $SRC/mapper.py,$SRC/reducer.py -mapper "python3 mapper.py hour" -reducer "python3 reducer.py" \
    "${cb[@]}" "${XS[@]}" -input $i -output $o > $l 2>&1
  echo "ELAPSED_SECONDS=$SECONDS" >> $l
}
runq2(){ # IN OUTBASE REDUCERS   (two-job chain)
  hdfs dfs -rm -r -f -skipTrash $2-j1 $2-j2 >/dev/null 2>&1
  hadoop jar $STREAM -D mapreduce.job.name=q2_job1 -D mapreduce.job.reduces=$3 -files $SRC/mapper.py,$SRC/reducer.py \
    -mapper "python3 mapper.py day" -reducer "python3 reducer.py" -combiner "python3 reducer.py" -input $1 -output $2-j1 > $R/q2_job1.log 2>&1
  hadoop jar $STREAM -D mapreduce.job.name=q2_job2 -D mapreduce.job.reduces=$3 -files $SRC/top_map.py,$SRC/top_reduce.py \
    -mapper "python3 top_map.py" -reducer "python3 top_reduce.py 5" -input $2-j1 -output $2-j2 > $R/q2_job2.log 2>&1
}
