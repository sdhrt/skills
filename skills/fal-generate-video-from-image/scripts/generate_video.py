#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "google-genai>=1.0.0",
#     "pillow>=10.0.0",
# ]
# ///
"""
Generate images using Google's Nano Banana Pro (Gemini 3 Pro Image) API.

Usage:
    uv run generate_image.py --prompt "your image description" --filename "output.png" [--resolution 1K|2K|4K] [--api-key KEY]
"""

import argparse
import os
import sys
from pathlib import Path


def get_api_key(provided_key: str | None) -> str | None:
    """Get API key from argument first, then environment."""
    if provided_key:
        return provided_key
    return os.environ.get("GEMINI_API_KEY")


def main():
    parser = argparse.ArgumentParser(
        description="Generate images using Nano Banana Pro (Gemini 3 Pro Image)"
    )
    parser.add_argument(
        "--prompt", "-p", required=True, help="Image description/prompt"
    )
    parser.add_argument(
        "--filename",
        "-f",
        required=True,
        help="Output filename (e.g., sunset-mountains.png)",
    )
    parser.add_argument(
        "--input-image", "-i", help="Optional input image path for editing/modification"
    )
    parser.add_argument(
        "--resolution",
        "-r",
        choices=["1K", "2K", "4K"],
        default="1K",
        help="Output resolution: 1K (default), 2K, or 4K",
    )
    parser.add_argument(
        "--api-key", "-k", help="Gemini API key (overrides FAL_API_KEY env var)"
    )

    args = parser.parse_args()

    # Get API key
    api_key = get_api_key(args.api_key)
    if not api_key:
        print("Error: No API key provided.", file=sys.stderr)
        print("Please either:", file=sys.stderr)
        print("  1. Provide --api-key argument", file=sys.stderr)
        print("  2. Set FAL_API_KEY environment variable", file=sys.stderr)
        sys.exit(1)

    import fal_client
