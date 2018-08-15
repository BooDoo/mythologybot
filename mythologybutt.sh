
#!/usr/bin/env sh
source ~/.cronrc;
TWEET=$(awk NR==$((${RANDOM} % `wc -l < new_motifs.txt` + 1)) new_motifs.txt | sed -r 's/(^\S+? )|(: |;|,|\?|!)| ([\(\"].{3,}[\)\"]) |\b(--|int?o?|about|while|he|she|they|s?o? ?that|as|who|by|when|for|witho?u?t?|at|on|and|because|but|to b?e?|from|under|has|where|of|or|whiche?v?e?r?)\b/\1\2\n\3\4/g');
echo Should tweet\n $TWEET;
twurl set default MythologyButt
twurl tweet -d "status=$TWEET" /1.1/statuses/update.json;
curl -H "Authorization: Bearer $MYTHOLOGYBUTT_MASTODON" -d "status=$TWEET" https://botsin.space/api/v1/statuses