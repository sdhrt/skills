#!/bin/bash
set -euo pipefail

# FAL AI Poll Script
# Checks status and fetches result for a Seedance 2.0 reference-to-video request.
# Usage: ./poll.sh --request-id <request-id> [--api-key <key>]
#
# Exit codes:
#   0 - completed, video CDN URL printed to stdout
#   1 - error (auth, content policy, unexpected)
#   2 - not ready yet (IN_QUEUE or IN_PROGRESS)

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--request-id) REQUEST_ID="$2"; shift 2 ;;
    -k|--api-key) API_KEY="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

if [[ -z "${API_KEY:-}" ]]; then
  API_KEY="${FAL_KEY:-}"
fi

if [[ -z "${API_KEY:-}" ]]; then
  echo "Error: No API key provided. Set FAL_KEY env var or use --api-key" >&2
  exit 1
fi

if [[ -z "${REQUEST_ID:-}" ]]; then
  echo "Error: --request-id is required" >&2
  exit 1
fi

# Polling uses the base model path (no endpoint suffix)
BASE_URL="https://queue.fal.run/bytedance/seedance-2.0/requests/$REQUEST_ID"
STATUS_URL="$BASE_URL/status"

echo "Checking status for request: $REQUEST_ID" >&2

# Step 1: GET status
status_response=$(curl -s --max-time 30 \
  -H "Authorization: Key $API_KEY" \
  -H "Content-Type: application/json" \
  "$STATUS_URL" 2>/dev/null) || true

if [[ -z "$status_response" ]]; then
  echo "Error: Empty response from status endpoint (network issue?)" >&2
  exit 2
fi

status=$(echo "$status_response" | python3 -c "import json, sys; print(json.load(sys.stdin).get('status', 'UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")
echo "Status: $status" >&2

case "$status" in
  "IN_QUEUE")
    queue_pos=$(echo "$status_response" | python3 -c "import json, sys; print(json.load(sys.stdin).get('queue_position', 'unknown'))" 2>/dev/null || echo "unknown")
    echo "Queue position: $queue_pos" >&2
    exit 2
    ;;
  "IN_PROGRESS")
    exit 2
    ;;
  "COMPLETED")
    ;;
  "UNKNOWN")
    echo "Could not parse status response:" >&2
    echo "$status_response" >&2
    exit 2
    ;;
  *)
    echo "Unexpected status: $status" >&2
    echo "$status_response" >&2
    exit 1
    ;;
esac

# Step 2: COMPLETED — fetch result
echo "Fetching result..." >&2
result=$(curl -s --max-time 30 \
  -H "Authorization: Key $API_KEY" \
  "$BASE_URL" 2>/dev/null) || true

if [[ -z "$result" ]]; then
  echo "Error: Empty response from result endpoint (network issue?)" >&2
  exit 2
fi

# Check for errors in result
if echo "$result" | python3 -c "import json, sys; data=json.load(sys.stdin); exit(0 if 'detail' in data else 1)" 2>/dev/null; then
  error_detail=$(echo "$result" | python3 -c "
import json, sys
data = json.load(sys.stdin)
detail = data.get('detail')
if isinstance(detail, list) and detail:
    e = detail[0]
    t = e.get('type', '')
    m = e.get('msg', str(e))
    print(('CONTENT_POLICY_VIOLATION: ' if 'content_policy_violation' in t else 'ERROR: ') + m)
elif isinstance(detail, str):
    print('ERROR: ' + detail)
else:
    print('ERROR: ' + str(detail))
" 2>/dev/null || echo "ERROR: Unknown error")
  echo "❌ $error_detail" >&2
  exit 1
fi

# Extract video URL
video_url=$(echo "$result" | python3 -c "
import json, sys
data = json.load(sys.stdin)
url = data.get('video', {}).get('url') or data.get('output', {}).get('video_url') or data.get('url')
if url:
    print(url)
" 2>/dev/null)

if [[ -n "$video_url" ]]; then
  echo "✅ Video ready!" >&2
  echo "$video_url"
  exit 0
fi

echo "Error: No video URL in completed response" >&2
echo "$result" >&2
exit 1
