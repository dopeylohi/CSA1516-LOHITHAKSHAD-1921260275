source ~/csa15_a5/Assignment5_Part2/scripts/lib.sh
IN=/transit/raw/gate_log_500mb.csv
hdfs dfs -test -e $IN || hdfs dfs -put -f $D/ds_500mb.csv $IN
echo $HDR > $R/combiner.csv
echo "[run] without combiner"; runq1 comb_no $IN /transit/out/comb_no 1 no;  csvrow $R/comb_no.log without >> $R/combiner.csv
echo "[run] with combiner";    runq1 comb_yes $IN /transit/out/comb_yes 1 yes; csvrow $R/comb_yes.log with >> $R/combiner.csv
column -s, -t $R/combiner.csv
cmp -s <(hdfs dfs -cat /transit/out/comb_no/part-* | LC_ALL=C sort) <(hdfs dfs -cat /transit/out/comb_yes/part-* | LC_ALL=C sort) && echo "Outputs identical with and without combiner" || echo "OUTPUTS DIFFER"
