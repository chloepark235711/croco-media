#!/bin/bash
# submit.sh ep scene  -> prints response json (budget checked by caller)
S=/tmp/claude-0/-home-user-croco-media/8d1d022b-9c3b-5ffe-bb65-4ab938ffa0c6/scratchpad
python3 $S/tools/prompts.py ${EP:-$1} ${SN:-$2} "$(cat $S/refurl)" > $S/body-$1-$2.json
curl -sS -m 60 -X POST https://api.higgsfield.ai/kling-video/v4.0/reference-to-video -H 'Content-Type: application/json' --data @$S/body-$1-$2.json -w '\nHTTP %{http_code}\n'
