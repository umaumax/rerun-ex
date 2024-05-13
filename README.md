# rerun-ex

## how to setup
``` bash
pip3 install rerun-sdk

pip3 install numpy
```

## how to run

``` bash
# default port is 9876
python3 -m rerun

cat test.csv | ./csv-pipe-rerun.py
```

``` bash
python3 -m rerun python3 -m rerun --port 9875

seq 1 100 | awk 'BEGIN{printf "id,a,b,c\n"; srand()} {printf "%d,%d,%d,%d\n", NR-1, int(rand()*10), int(rand()*50), int(rand()*100)}' | ./csv-pipe-rerun.py --addr 127.0.0.1:9875
```
