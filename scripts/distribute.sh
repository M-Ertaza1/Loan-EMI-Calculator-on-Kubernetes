#!/bin/bash
# Sends 30 POST requests via the Ingress and counts requests per pod
for i in $(seq 30); do
  curl -s -X POST http://emi.local/api/emi \
    -H 'Content-Type: application/json' \
    -d '{"principal":500000,"rate":12,"months":24}' | jq -r .servedBy
done | sort | uniq -c
