# CSA15 Assignment 5 - Part B (Hadoop 3.3.6, pseudo-distributed on WSL2 Ubuntu 24.04)
Record layout (assumed): timestamp,station_id,gate_id,card_id,tap_type,fare
- src/: generator, Hadoop Streaming mapper/reducer (reducer is also the combiner), Top-N chain, independent verifier, skew predictor
- scripts/: lib.sh, data.sh, b1.sh, b2_tests.sh, b2_combiner.sh, b3_scale.sh, b3_skew.sh, b4_failure.sh, b4_sched.sh
- conf/: Hadoop config files used (single queue, FIFO, two-queue Capacity)
- tests/: hand-checkable inputs and expected outputs
- results/: job logs with counters, fsck output, scaling.csv, skew and failure results
Run order: scripts/data.sh, b1, b2_tests, b2_combiner, b3_scale, b3_skew, b4_failure, b4_sched. Seeds: 42 (scaling), 5 (Top-N), 7 (skew).
