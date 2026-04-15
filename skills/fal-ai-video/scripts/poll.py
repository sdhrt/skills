#!/usr/bin/env python3
# pyright: basic
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fal-client>=0.5.0",
# ]
# ///
"""
Check status and retrieve result for a Seedance 2.0 request.

Usage:
    uv run get_video_result.py --request-id "your-request-id" [--api-key KEY]

Checks status first. If completed, prints the video CDN URL to stdout.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

FAL_MODEL_ID = "bytedance/seedance-2.0/image-to-video"
FAL_QUEUE_BASE = "https://queue.fal.run"


def get_api_key(provided_key: str | None) -> str | None:
    """Get API key from argument first, then environment."""
    if provided_key:
        return provided_key
    return os.environ.get("FAL_KEY")


def fal_request(url: str, api_key: str) -> dict:
    """Make an authenticated GET request to fal.ai queue API."""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Key {api_key}",
            "Content-Type": "application/json",
        },
        method="GET",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def main():
    parser = argparse.ArgumentParser(
        description="Get Seedance 2.0 video result from fal.ai queue"
    )
    parser.add_argument(
        "--request-id", "-r", required=True, help="Request ID from submit_video.py"
    )
    parser.add_argument(
        "--api-key", "-k", help="fal.ai API key (overrides FAL_KEY env var)"
    )

    args = parser.parse_args()

    # Get API key
    api_key = get_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided.", file=sys.stderr)
        print("Please either:", file=sys.stderr)
        print("  1. Provide --api-key argument", file=sys.stderr)
        print("  2. Set FAL_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    request_id = args.request_id

    # Check status first
    status_url = f"{FAL_QUEUE_BASE}/{FAL_MODEL_ID}/requests/{request_id}/status?logs=1"
    print(f"Checking status for request: {request_id}", file=sys.stderr)

    try:
        status_resp = fal_request(status_url, api_key)
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"Error checking status: HTTP {e.code} - {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error checking status: {e}", file=sys.stderr)
        sys.exit(1)

    status = status_resp.get("status")
    print(f"Status: {status}", file=sys.stderr)

    # Print any logs
    for log in status_resp.get("logs", []):
        print(
            f"  [{log.get('timestamp', '')}] {log.get('message', '')}", file=sys.stderr
        )

    if status == "IN_QUEUE":
        position = status_resp.get("queue_position", "unknown")
        print(f"Queue position: {position}", file=sys.stderr)
        print("Request is still in queue. Try again later.", file=sys.stderr)
        sys.exit(2)

    if status == "IN_PROGRESS":
        print("Request is still processing. Try again later.", file=sys.stderr)
        sys.exit(2)

    if status != "COMPLETED":
        print(f"Unexpected status: {status}", file=sys.stderr)
        print(json.dumps(status_resp, indent=2), file=sys.stderr)
        sys.exit(1)

    # Status is COMPLETED — fetch the result
    result_url = f"{FAL_QUEUE_BASE}/{FAL_MODEL_ID}/requests/{request_id}"
    print("Fetching result...", file=sys.stderr)

    try:
        result_resp = fal_request(result_url, api_key)
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"Error fetching result: HTTP {e.code} - {body}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error fetching result: {e}", file=sys.stderr)
        sys.exit(1)

    # Extract the video URL from the response
    video_url = result_resp.get("video", {}).get("url")
    seed = result_resp.get("seed")

    if not video_url:
        print("Error: No video URL found in response.", file=sys.stderr)
        print(json.dumps(result_resp, indent=2), file=sys.stderr)
        sys.exit(1)

    # Print video URL to stdout (capturable by shell)
    print(video_url)
    if seed is not None:
        print(f"Seed: {seed}", file=sys.stderr)
    print(f"Video URL: {video_url}", file=sys.stderr)


if __name__ == "__main__":
    main()
