#!/bin/bash
# submit.sh ep scene
S=${S:?scratchpad dir}
python3 $S/tools/prompts.py $1 $2 $(cat $S/refs) > $S/body-$1-$2.json
curl -sS -m 60 -X POST https://api.higgsfield.ai/kling-video/v4.0/reference-to-video -H 'Content-Type: application/json' --data @$S/body-$1-$2.json -w '\nHTTP %{http_code}\n'
