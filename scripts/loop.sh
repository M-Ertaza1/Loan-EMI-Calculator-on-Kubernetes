#!/bin/bash
# Continuous request loop: prints timestamp and HTTP status for every request
while true; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -m 5 -X POST http://emi.local/api/emi \
    -H 'Content-Type: application/json' \
    -d '{"principal":500000,"rate":12,"months":24}')
  echo "$(date +%T) $code"
  sleep 0.2
done
