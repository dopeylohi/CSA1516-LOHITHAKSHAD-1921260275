import math
MB_PER_TB = 1024*1024   # assumed: 1 TB = 1024 GB
daily_mb=2*MB_PER_TB; block_mb=128; rep=3; days=90; node_tb=24; headroom=0.25; obj=150
print("A2.1 capacity planning (assumed 1 TB = 1024 GB)")
blocks_day=math.ceil(daily_mb/block_mb)
print(f"1. blocks/day = {daily_mb} MB / {block_mb} MB = {blocks_day}")
raw_day=2*rep; raw_90=raw_day*days
print(f"2. raw/day after replication = 2 TB x {rep} = {raw_day} TB; {days} days = {raw_day} x {days} = {raw_90} TB (logical {2*days} TB)")
usable=node_tb*(1-headroom); nodes=math.ceil(raw_90/usable)
print(f"3. usable per node = {node_tb} x (1-{headroom}) = {usable} TB; nodes = {raw_90}/{usable} = {raw_90/usable:.2f} -> {nodes}")
b90=blocks_day*days; nn=b90*obj
print(f"4. blocks in {days} days = {blocks_day} x {days} = {b90}; NameNode memory = {b90} x {obj} B = {nn} B = {nn/1024**2:.1f} MiB ({nn/1024**3:.3f} GiB)")
file_kb=100
fd=daily_mb*1024/file_kb; f90=fd*days; nt=f90*2*obj
print(f"5. tiny files (assumed {file_kb} KB each): files/day = {fd:,.0f}; {days} days = {f90:,.0f}; memory = files x (1 file object + 1 block object) x {obj} B = {nt/1024**3:,.0f} GiB")
print(f"   same data in 128 MB blocks needs {nn/1024**3:.3f} GiB, so tiny files need about {nt/nn:,.0f}x more")
