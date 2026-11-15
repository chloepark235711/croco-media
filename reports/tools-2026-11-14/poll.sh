#!/bin/bash
# usage: poll.sh request_id
for i in $(seq 1 60); do
  s=$(curl -sS -m 30 https://api.higgsfield.ai/requests/$1/status)
  st=$(echo "$s" | python3 -c "import json,sys;print(json.load(sys.stdin).get('status'))")
  if [ "$st" != "queued" ] && [ "$st" != "in_progress" ]; then echo "$s"; exit 0; fi
  sleep 15
done
echo TIMEOUT
