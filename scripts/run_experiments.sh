#!/bin/bash
cd ~/emi-assignment/scripts
kubectl delete hpa emi-web -n emi 2>/dev/null
for N in 1 2 3; do
  kubectl scale deployment emi-web --replicas=$N -n emi
  kubectl rollout status deployment/emi-web -n emi
  sleep 20
  for R in 10 25 50 100 200; do
    D=../results/runs/${N}rep_${R}rps
    mkdir -p $D
    echo "=== replicas=$N rate=$R $(date +%T)"
    python3 monitor.py $D & MP=$!
    sleep 3
    ./load.sh $R 60 $D
    sleep 16
    kill -TERM $MP 2>/dev/null; wait $MP 2>/dev/null
    sleep 30
  done
done
kubectl scale deployment emi-web --replicas=3 -n emi
echo "ALL DONE $(date +%T)"
