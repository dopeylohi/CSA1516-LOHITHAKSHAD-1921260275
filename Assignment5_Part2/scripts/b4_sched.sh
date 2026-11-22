source ~/csa15_a5/Assignment5_Part2/scripts/lib.sh
YS=$HADOOP_CONF_DIR/yarn-site.xml; CS=$HADOOP_CONF_DIR/capacity-scheduler.xml
cp $CS $W/capacity-scheduler.single.xml; cp $YS $W/yarn-site.orig.xml
restart_rm(){ yarn --daemon stop resourcemanager; sleep 3; yarn --daemon start resourcemanager
  until yarn node -list 2>/dev/null | grep -q RUNNING; do sleep 3; done; sleep 5; }
sched_test(){ # LABEL LONGQ SHORTQ
  echo "=== $1 (long: 2 GB job in queue $2; short: 100 MB job in queue $3, submitted 30 s later)"
  ( runq1 $1_long /transit/raw/ds_2000mb.csv /transit/out/$1_long 1 yes -D mapreduce.job.queuename=$2 ) &
  sleep 30
  ( runq1 $1_short /transit/raw/ds_100mb.csv /transit/out/$1_short 1 yes -D mapreduce.job.queuename=$3 ) &
  echo ">>> both jobs are running now: open http://localhost:8088/cluster/scheduler and take the screenshot"
  wait
  echo "RESULT $1: short job finished in $(ctr $R/$1_short.log ELAPSED_SECONDS) s, long job in $(ctr $R/$1_long.log ELAPSED_SECONDS) s"
}
# 1) single queue, FIFO scheduler
sed -i 's#</configuration>#<property><name>yarn.resourcemanager.scheduler.class</name><value>org.apache.hadoop.yarn.server.resourcemanager.scheduler.fifo.FifoScheduler</value></property></configuration>#' $YS
cp $YS $A/conf/yarn-site.fifo.xml; restart_rm; sched_test fifo default default
# 2) Capacity scheduler, two queues: batch 70% (hard cap 70%), adhoc 30% (may grow to 100%)
cp $W/yarn-site.orig.xml $YS
cat > $CS <<'XML'
<?xml version="1.0"?><configuration>
<property><name>yarn.scheduler.capacity.root.queues</name><value>batch,adhoc</value></property>
<property><name>yarn.scheduler.capacity.root.batch.capacity</name><value>70</value></property>
<property><name>yarn.scheduler.capacity.root.batch.maximum-capacity</name><value>70</value></property>
<property><name>yarn.scheduler.capacity.root.adhoc.capacity</name><value>30</value></property>
<property><name>yarn.scheduler.capacity.root.adhoc.maximum-capacity</name><value>100</value></property>
<property><name>yarn.scheduler.capacity.root.batch.acl_submit_applications</name><value>*</value></property>
<property><name>yarn.scheduler.capacity.root.adhoc.acl_submit_applications</name><value>*</value></property>
<property><name>yarn.scheduler.capacity.maximum-am-resource-percent</name><value>0.5</value></property>
<property><name>yarn.scheduler.capacity.resource-calculator</name><value>org.apache.hadoop.yarn.util.resource.DefaultResourceCalculator</value></property>
</configuration>
XML
cp $CS $A/conf/capacity-scheduler.two-queue.xml; restart_rm
yarn queue -status batch 2>/dev/null | grep -E "Queue Name|Capacity|Maximum"; yarn queue -status adhoc 2>/dev/null | grep -E "Queue Name|Capacity|Maximum"
sched_test capacity batch adhoc
# restore the single default queue so earlier steps still work
cp $W/capacity-scheduler.single.xml $CS; restart_rm
