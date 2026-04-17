#!/usr/bin/env python3
# pyright: basic
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "Pillow>=10.0.0",
# ]
# ///
"""
Add a dense white grid overlay to an image.

Usage:
    uv run grid_overlay.py --image "path/to/image.png" [--output "path/to/output.png"] [--spacing 40] [--thickness 4] [--opacity 200]

Prints the output file path to stdout on success.
"""

import argparse
import os
import sys
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(
        description="Add a dense white grid overlay to an image"
    )
    parser.add_argument(
        "--image", "-i", required=True, help="Input image path (local file)"
    )
    parser.add_argument(
        "--output", "-o", help="Output image path (default: timestamped filename alongside input)"
    )
    parser.add_argument(
        "--spacing", "-s", type=int, default=40,
        help="Grid cell size in pixels (default: 40 — dense)"
    )
    parser.add_argument(
        "--thickness", "-t", type=int, default=4,
        help="Grid line thickness in pixels (default: 4 — thick)"
    )
    parser.add_argument(
        "--opacity", type=int, default=200,
        help="Grid line opacity 0-255 (default: 200 — semi-opaque, obstructs content)"
    )

    args = parser.parse_args()

    # Validate input
    if not os.path.isfile(args.image):
        print(f"Error: Input image not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    if not (0 <= args.opacity <= 255):
        print("Error: --opacity must be between 0 and 255", file=sys.stderr)
        sys.exit(1)

    # Import after validation to avoid slow import on bad args
    from PIL import Image, ImageDraw

    # Load image
    print(f"Loading image: {args.image}", file=sys.stderr)
    img = Image.open(args.image).convert("RGBA")
    width, height = img.size
    print(f"Image size: {width}x{height}", file=sys.stderr)

    # Create transparent grid layer
    grid_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(grid_layer)

    line_color = (255, 255, 255, args.opacity)

    # Draw vertical lines
    x = 0
    while x <= width:
        draw.line([(x, 0), (x, height)], fill=line_color, width=args.thickness)
        x += args.spacing

    # Draw horizontal lines
    y = 0
    while y <= height:
        draw.line([(0, y), (width, y)], fill=line_color, width=args.thickness)
        y += args.spacing

    # Composite grid over image
    result = Image.alpha_composite(img, grid_layer)

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        input_dir = os.path.dirname(os.path.abspath(args.image))
        output_path = os.path.join(input_dir, f"{timestamp}-grid-overlay.png")

    # Save as PNG to preserve transparency metadata; convert back if input was JPEG
    ext = os.path.splitext(output_path)[1].lower()
    if ext in (".jpg", ".jpeg"):
        result = result.convert("RGB")

    result.save(output_path)
    print(f"Saved: {output_path}", file=sys.stderr)

    # Print output path to stdout (capturable by shell)
    print(output_path)


if __name__ == "__main__":
    main()
