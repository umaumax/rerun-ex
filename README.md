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

Can send data over the network by specifying IP address and port
``` bash
python3 -m rerun python3 -m rerun --port 9875

seq 1 100 | awk 'BEGIN{printf "id,a,b,c\n"; srand()} {printf "%d,%d,%d,%d\n", NR-1, int(rand()*10), int(rand()*50), int(rand()*100)}' | ./csv-pipe-rerun.py --addr 127.0.0.1:9875
```

Data can be sent from different clients if the same `recording_id` is specified
``` bash
python3 -m rerun python3 -m rerun

seq 1 100 | awk 'BEGIN{printf "id,fuga-a,fuga-b,fuga-c\n"; srand()} {printf "%d,%d,%d,%d\n", NR-1, int(rand()*10), int(rand()*50), int(rand()*30)}' | ./csv-pipe-rerun.py --addr 127.0.0.1:9876 --interval 0.2 -t fuga --recording_id=test
seq 1 100 | awk 'BEGIN{printf "id,hoge-a,hoge-b,hoge-c\n"; srand()} {printf "%d,%d,%d,%d\n", NR-1, int(rand()*20), int(rand()*80), int(rand()*90)}' | ./csv-pipe-rerun.py --addr 127.0.0.1:9876 --interval 0.2 -t hoge --recording_id=test
```
