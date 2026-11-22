source ~/csa15_a5/env.sh; cd $D; df -h . | tail -1; G=$A/src/generator.py
for s in 100 500 1000 2000; do [ -f ds_${s}mb.csv ] || { echo "[gen] ${s} MB"; python3 $G ds_${s}mb.csv $s --seed 42; }; done
python3 $G topn_20mb.csv 20 --days 3 --seed 5
python3 $G skew_uniform_500mb.csv 500 --days 1 --seed 7
python3 $G skew_hot_500mb.csv 500 --days 1 --hot 0.7 --seed 7
ls -lh *.csv; head -3 ds_100mb.csv; wc -l ds_100mb.csv
