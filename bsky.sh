#!/usr/bin/env bash

# shamelessly stolen from
# https://gist.github.com/pojntfx/72403066a96593c1ba8fd5df2b531f2d
# this takes the TWEET variable from the mythologybot.sh script and pushes it out to bsky

# Resolve DID for handle
DID_URL="https://bsky.social/xrpc/com.atproto.identity.resolveHandle"
export DID=$(curl -s -G \
  --data-urlencode "handle=$BSKY_USERNAME" \
  "$DID_URL" | jq -r .did)

# Get API key with the app password
API_KEY_URL='https://bsky.social/xrpc/com.atproto.server.createSession'
POST_DATA='{ "identifier": "'"${DID}"'", "password": "'"${BSKY_PASSWORD}"'" }'
export API_KEY=$(curl -s -X POST \
  -H 'Content-Type: application/json' \
  -d "$POST_DATA" \
  "$API_KEY_URL" | jq -r .accessJwt)

POST_FEED_URL='https://bsky.social/xrpc/com.atproto.repo.createRecord'
POST_RECORD='{ "collection": "app.bsky.feed.post", "repo": "'"${DID}"'", "record": { "text": "'"${TWEET//$'\n'/\\n}"'", "createdAt": "'"$(date +%Y-%m-%dT%H:%M:%S.%3NZ)"'", "$type": "app.bsky.feed.post" } }'

curl -s -X POST \
  -H "Authorization: Bearer ${API_KEY}" \
  -H 'Content-Type: application/json' \
  -d "$POST_RECORD" \
  "$POST_FEED_URL" | jq -c
