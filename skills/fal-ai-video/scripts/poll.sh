#!/bin/bash
set -euo pipefail

# FAL AI Poll Script
# Fallback script for checking Seedance 2.0 video generation status
# Usage: ./poll.sh --request-id <request-id> [--api-key <key>]

# Parse arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    -r|--request-id) REQUEST_ID="$2"; shift 2 ;;
    -k|--api-key) API_KEY="$2"; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

# Get API key from env if not provided
if [[ -z "${API_KEY:-}" ]]; then
  if [[ -n "${FAL_KEY:-}" ]]; then
    API_KEY="$FAL_KEY"
  else
    echo "Error: No API key provided. Set FAL_KEY env var or use --api-key" >&2
    exit 1
  fi
fi

if [[ -z "${REQUEST_ID:-}" ]]; then
  echo "Error: --request-id is required" >&2
  exit 1
fi

FAL_MODEL_ID="bytedance/seedance-2.0"
FAL_QUEUE_BASE="https://queue.fal.run"

echo "Checking status for request: $REQUEST_ID" >&2

# Function to make API calls with error handling
fal_request() {
  local url="$1"
  local method="${2:-GET}"

  # Use curl with -f to fail on HTTP errors >400
  curl -s -X "$method" \
    -H "Authorization: Key $API_KEY" \
    -H "Content-Type: application/json" \
    "$url" 2>/dev/null || true
}

# Try GET on the result endpoint
echo "Checking result endpoint..." >&2
response=$(fal_request "$FAL_QUEUE_BASE/$FAL_MODEL_ID/requests/$REQUEST_ID" "GET")

# Check if response contains error details
if echo "$response" | python3 -c "import json, sys; data=json.load(sys.stdin); exit(0 if 'detail' in data else 1)" 2>/dev/null; then
  # Extract error detail
  error_detail=$(echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    detail = data.get('detail')
    if isinstance(detail, list) and len(detail) > 0:
        error_obj = detail[0]
        msg = error_obj.get('msg', str(error_obj))
        error_type = error_obj.get('type', '')
        if 'content_policy_violation' in str(error_type):
            print('CONTENT_POLICY_VIOLATION: ' + msg)
        else:
            print('ERROR: ' + msg)
    elif isinstance(detail, str):
        print('ERROR: ' + detail)
    else:
        print('ERROR: ' + str(detail))
except Exception as e:
    print('ERROR: Failed to parse error - ' + str(e))
" 2>/dev/null || echo "ERROR: Unknown error")

  echo "❌ Request failed: $error_detail" >&2
  exit 1
fi

# Check if response contains video URL (success case)
video_url=$(echo "$response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    video_url = data.get('video', {}).get('url') or data.get('output', {}).get('video_url') or data.get('url')
    if video_url:
        print(video_url)
except:
    pass
" 2>/dev/null)

if [[ -n "$video_url" ]]; then
  echo "✅ Video ready!" >&2
  echo "$video_url"
  exit 0
fi

# If neither error nor success, check queue status with POST
echo "Checking queue status with POST..." >&2
post_response=$(curl -s -X POST \
  -H "Authorization: Key $API_KEY" \
  -H "Content-Type: application/json" \
  "$FAL_QUEUE_BASE/$FAL_MODEL_ID/image-to-video/requests/$REQUEST_ID" 2>/dev/null || echo "{}")

if [[ "$post_response" != "{}" ]]; then
  status=$(echo "$post_response" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('status', 'UNKNOWN'))" 2>/dev/null || echo "UNKNOWN")

  case "$status" in
    "IN_QUEUE")
      queue_pos=$(echo "$post_response" | python3 -c "import json, sys; data=json.load(sys.stdin); print(data.get('queue_position', 'unknown'))" 2>/dev/null || echo "unknown")
      echo "Queue status: IN_QUEUE (position: $queue_pos)" >&2
      exit 2
      ;;
    "IN_PROGRESS")
      echo "Status: IN_PROGRESS" >&2
      exit 2
      ;;
    "COMPLETED")
      # Try to extract URL from POST response
      video_url=$(echo "$post_response" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    video_url = data.get('video', {}).get('url') or data.get('output', {}).get('video_url') or data.get('url')
    if video_url:
        print(video_url)
except:
    pass
" 2>/dev/null)

      if [[ -n "$video_url" ]]; then
        echo "✅ Video ready!" >&2
        echo "$video_url"
        exit 0
      fi
      exit 2
      ;;
    *)
      echo "Unknown queue status: $status" >&2
      exit 2
      ;;
  esac
else
  echo "Failed to check queue status" >&2
  exit 2
