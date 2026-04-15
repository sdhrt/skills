#!/usr/bin/env python3
# pyright: basic
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fal-client>=0.5.0",
# ]
# ///
"""
Submit an image-to-video request to fal.ai Seedance 2.0 (async queue).

Usage:
    uv run submit_video.py --prompt "motion description" --image "path/to/image.png" [--resolution 480p|720p] [--duration auto|4-15]

Prints the request_id to stdout on success.
"""

import argparse
import os
import sys

FAL_MODEL_ID = "bytedance/seedance-2.0/image-to-video"


def get_api_key(provided_key: str | None) -> str | None:
    """Get API key from argument first, then environment."""
    if provided_key:
        return provided_key
    return os.environ.get("FAL_KEY")


def main():
    parser = argparse.ArgumentParser(
        description="Submit image-to-video request to Seedance 2.0 (fal.ai)"
    )
    parser.add_argument(
        "--prompt", "-p", required=True, help="Motion/action description for the video"
    )
    parser.add_argument(
        "--image", "-i", required=True, help="Input image path (local file) to animate"
    )
    parser.add_argument(
        "--resolution",
        "-r",
        choices=["480p", "720p"],
        default="720p",
        help="Video resolution: 480p (faster) or 720p (default)",
    )
    parser.add_argument(
        "--duration",
        "-d",
        choices=[
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
        ],
        default="5",
        help="Video duration in seconds (default: auto)",
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

    # Set the key in env so fal_client picks it up
    os.environ["FAL_KEY"] = api_key

    # Validate input image exists
    if not os.path.isfile(args.image):
        print(f"Error: Input image not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    # Import here after validation to avoid slow import on error
    import fal_client

    # Upload the local image to fal CDN
    print(f"Uploading image: {args.image}", file=sys.stderr)
    try:
        image_url = fal_client.upload_file(args.image)
        print(f"Uploaded to: {image_url}", file=sys.stderr)
    except Exception as e:
        print(f"Error uploading image: {e}", file=sys.stderr)
        sys.exit(1)

    # Build request arguments
    arguments = {
        "prompt": args.prompt,
        "image_url": image_url,
        "resolution": args.resolution,
        "duration": args.duration,
    }

    # Submit to queue
    print(f"Submitting to {FAL_MODEL_ID}...", file=sys.stderr)
    try:
        handler = fal_client.submit(FAL_MODEL_ID, arguments=arguments)
        request_id = handler.request_id
    except Exception as e:
        print(f"Error submitting request: {e}", file=sys.stderr)
        sys.exit(1)

    # Print request_id to stdout (capturable by shell)
    print(request_id)
    print(f"Request submitted. request_id: {request_id}", file=sys.stderr)


if __name__ == "__main__":
    main()
