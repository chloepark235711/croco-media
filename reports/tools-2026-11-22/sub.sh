#!/bin/bash
S=/tmp/claude-0/-home-user-croco-media/6f50a2d8-a8c8-56f3-8c4c-0edee9f177bb/scratchpad
python3 $S/tools/ep.py $1 $2 $(cat $S/refs) > $S/body-$1-$2.json
curl -sS -m 60 -X POST https://api.higgsfield.ai/kling-video/v4.0/reference-to-video -H 'Content-Type: application/json' --data @$S/body-$1-$2.json -w '\nHTTP %{http_code}\n'
