#!/usr/bin/env sh
source ~/.cronrc;
export TWEET=$(awk NR==$((${RANDOM} % `wc -l < motifs.txt` + 1)) motifs.txt | sed -r 's/(^\S+? )|(: |;|,|\?|!)| ([\(\"].{3,}[\)\"]) |\b(--|int?o?|about|while|he|she|they|s?o? ?that|as|who|by|when|for|witho?u?t?|at|on|and|because|but|to b?e?|from|under|has|where|how many|how long|of|or|whiche?v?e?r?)\b/\1\2\n\3\4/g');
echo -en Should tweet\n $TWEET;
twurl set default MythologyBot
twurl '/2/tweets' --data '{"text": "'"${TWEET//$'\n'/\\n}"'"}' --header 'Content-Type: application/json' --consumer-key ${MYTHBOT_CONSUMERKEY} --consumer-secret ${MYTHBOT_CONSUMERSECRET} --access-token ${MYTHBOT_ACCESSTOKEN} --token-secret ${MYTHBOT_TOKENSECRET}
curl -H "Authorization: Bearer $MYTHOLOGYBOT_MASTODON" -d "status=$TWEET" https://botsin.space/api/v1/statuses
/home/boodoo/apps/mythology/bsky.sh
