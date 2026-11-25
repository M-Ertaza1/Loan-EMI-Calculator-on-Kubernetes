#!/bin/bash
cd ~/emi-assignment/scripts
D=../results/autoscale; mkdir -p $D
kubectl scale deployment emi-web --replicas=1 -n emi
kubectl rollout status deployment/emi-web -n emi
cp ../k8s/05-hpa.yaml.disabled ../k8s/05-hpa.yaml
kubectl apply -f ../k8s/05-hpa.yaml
sleep 30
python3 monitor.py $D --hpa & MP=$!
echo "timestamp,phase,rate" > $D/phases.csv
phase() {  # rate seconds
  echo "$(date +%s),start,$1" >> $D/phases.csv
  ./load.sh $1 $2 $D/load_$1rps_$(date +%H%M%S)
  echo "$(date +%s),end,$1" >> $D/phases.csv
}
phase 10 120
phase 100 300
phase 10 180
sleep 20
kill -TERM $MP 2>/dev/null; wait $MP 2>/dev/null
echo "AUTOSCALE DONE"
