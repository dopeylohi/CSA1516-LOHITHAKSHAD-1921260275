source ~/csa15_a5/env.sh; cd $A
for n in b1 b2_tests b2_combiner b3_scale b3_skew b4_failure b4_sched; do
  echo "[$(date +%H:%M)] running $n"; bash scripts/$n.sh 2>&1 | tee results/out_$n.txt >/dev/null
done
{ echo "######## data"; ls -lh $D/*.csv; head -3 $D/ds_100mb.csv
  for n in b1 b2_tests b2_combiner b3_scale b3_skew b4_failure b4_sched; do echo; echo "######## $n"; cat results/out_$n.txt; done; } > results/SUMMARY.txt
echo "ALL DONE - results/SUMMARY.txt is ready"
