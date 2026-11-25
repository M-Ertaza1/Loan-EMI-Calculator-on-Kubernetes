#!/bin/bash
# usage: load.sh RATE SECONDS OUTDIR
cd ~/emi-assignment/scripts
R=$1; T=$2; D=$3
mkdir -p $D
TOTAL=$((R*T))
K=$(( (TOTAL + 999) / 1000 ))
S=$(( TOTAL / K ))
RATE=$(python3 -c "print($R/$K)")
python3 gen_sessions.py $S
for i in $(seq $K); do
  httperf --server emi.local --port 80 --hog --wsesslog=$S,0,sessions.txt \
    --add-header='Content-Type: application/json\n' \
    --rate=$RATE --timeout 5 > $D/httperf_$i.txt 2>&1 &
done
wait
