#!/usr/bin/env python3
# pyright: basic
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "fal-client>=0.5.0",
# ]
# ///
"""
Submit a reference-to-video request to fal.ai Seedance 2.0 (async queue).

Usage:
    uv run submit_video.py --prompt "motion description" --image img1.png [--image img2.png ...] \
        [--video vid.mp4 ...] [--audio audio.mp3 ...] \
        [--resolution 480p|720p|1080p] [--duration auto|4-15] \
        [--aspect-ratio auto|21:9|16:9|1:1|9:16] [--no-audio] [--seed 42]

Prints the request_id to stdout on success.
"""

import argparse
import os
import sys

FAL_MODEL_ID = "bytedance/seedance-2.0/reference-to-video"


def get_api_key(provided_key: str | None) -> str | None:
    """Get API key from argument first, then environment."""
    if provided_key:
        return provided_key
    return os.environ.get("FAL_KEY")


def main():
    parser = argparse.ArgumentParser(
        description="Submit reference-to-video request to Seedance 2.0 (fal.ai)"
    )
    parser.add_argument(
        "--prompt", "-p", required=True, help="Motion/action description for the video (use @Image1, @Video1, @Audio1 to reference inputs)"
    )
    parser.add_argument(
        "--image", "-i", action="append", default=[], help="Reference image path (repeatable, max 9). Use @Image1..@Image9 in prompt."
    )
    parser.add_argument(
        "--video", "-v", action="append", default=[], help="Reference video path (repeatable, max 3, combined 2-15s). Use @Video1..@Video3 in prompt."
    )
    parser.add_argument(
        "--audio", "-a", action="append", default=[], help="Reference audio path (repeatable, max 3, combined ≤15s, mp3/wav). Use @Audio1..@Audio3 in prompt."
    )
    parser.add_argument(
        "--resolution",
        "-r",
        choices=["480p", "720p", "1080p"],
        default="720p",
        help="Video resolution (default: 720p)",
    )
    parser.add_argument(
        "--duration",
        "-d",
        choices=["auto"] + [str(s) for s in range(4, 16)],
        default="5",
        help="Video duration in seconds, or 'auto' (default: 5)",
    )
    parser.add_argument(
        "--aspect-ratio",
        choices=["auto", "21:9", "16:9", "1:1", "9:16"],
        default=None,
        help="Aspect ratio (default: auto)",
    )
    parser.add_argument(
        "--no-audio", action="store_true", help="Disable audio generation"
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="Seed for reproducibility"
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

    if not args.image and not args.video:
        print("Error: At least one --image or --video is required.", file=sys.stderr)
        sys.exit(1)

    # Validate all local files exist
    for paths, label in [(args.image, "image"), (args.video, "video"), (args.audio, "audio")]:
        for p in paths:
            if not os.path.isfile(p):
                print(f"Error: {label} file not found: {p}", file=sys.stderr)
                sys.exit(1)

    # Import here after validation to avoid slow import on error
    import fal_client

    def upload_files(paths: list[str], label: str) -> list[str]:
        urls = []
        for p in paths:
            print(f"Uploading {label}: {p}", file=sys.stderr)
            url = fal_client.upload_file(p)
            print(f"  → {url}", file=sys.stderr)
            urls.append(url)
        return urls

    try:
        image_urls = upload_files(args.image, "image")
        video_urls = upload_files(args.video, "video")
        audio_urls = upload_files(args.audio, "audio")
    except Exception as e:
        print(f"Error uploading file: {e}", file=sys.stderr)
        sys.exit(1)

    # Build request arguments
    arguments: dict = {
        "prompt": args.prompt,
        "resolution": args.resolution,
        "duration": args.duration,
    }
    if image_urls:
        arguments["image_urls"] = image_urls
    if video_urls:
        arguments["video_urls"] = video_urls
    if audio_urls:
        arguments["audio_urls"] = audio_urls
    if args.aspect_ratio:
        arguments["aspect_ratio"] = args.aspect_ratio
    if args.no_audio:
        arguments["generate_audio"] = False
    if args.seed is not None:
        arguments["seed"] = args.seed

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
