---
name: grid-overlay
description: Use when the user wants to add a white grid overlay to a photo or image. Supports Telegram/chat image input. Dense, thick lines that partially obscure the content.
---

# Grid Overlay

Add a dense white grid over a photo using Python and Pillow. Lines are thick and close together to visibly obstruct the image content.

## Workflow (single-step sync)

One script does everything: `grid_overlay.py` — loads the image, draws the grid, saves the result, prints the output path.

### Step 1: Save the input image (if received from Telegram or chat)

First ask user to confirm if there already is a grid overlay in the image they provided. If they say there already is a grid, please terminate and no need to run this skill.

### Step 2: Save the input image (if received from Telegram or chat)

If the user sends an image in chat (e.g. Telegram), save it to disk first before calling the script. Save to the user's current working directory with a descriptive filename:

```bash
# Use a timestamped name to avoid collisions
SAVE_PATH="$(pwd)/yyyy-mm-dd-hh-mm-ss-input.png"
```

If the user provides a path to an existing file on disk, use that path directly — do not re-save.

### Step 3: Run the script

Run using the absolute path (do NOT cd to the skill directory first).
If `uv` doesn't exist, install it first:

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
OUTPUT=$(uv run skills/grid-overlay/scripts/grid_overlay.py \
  --image "/path/to/image.png" \
  [--output "/path/to/output.png"] \
  [--spacing 40] \
  [--thickness 4] \
  [--opacity 200])
```

The output file path is printed to stdout. Informational messages go to stderr.

## Parameters

### Required
- **`--image`** (`-i`): Local path to the input image. Supported formats: JPEG, PNG, WebP.

### Optional
- **`--output`** (`-o`): Output file path. Defaults to a timestamped `yyyy-mm-dd-hh-mm-ss-grid-overlay.png` alongside the input file.
- **`--spacing`** (`-s`): Grid cell size in pixels. Default: `40` (dense). Smaller = more lines.
- **`--thickness`** (`-t`): Line thickness in pixels. Default: `4` (thick).
- **`--opacity`**: Line opacity, 0–255. Default: `200` (semi-opaque, visibly obstructs content).

## Parameter Mapping

Map user requests to parameters:

| User says | Parameters |
|-----------|-----------|
| "dense", "tight", "lots of lines" | `--spacing 25` |
| "sparse", "loose" | `--spacing 80` |
| "thick lines" | `--thickness 6` or `--thickness 8` |
| "thin lines" | `--thickness 2` |
| "subtle", "light grid" | `--opacity 100` |
| "heavy", "strong grid" | `--opacity 230` |
| No preference | Use defaults (spacing=40, thickness=4, opacity=200) |

## Handling Telegram / Chat Images

When the user sends an image through Telegram or any chat interface:

1. Determine where the image data is (file path, base64, or binary blob)
2. Save it to disk as a PNG or JPEG if not already on disk
3. Use the saved file path as the `--image` argument

## Output

- Script prints the output file path to stdout
- Share the file path with the user or send the file back through the chat interface
- Output is always PNG unless `--output` specifies a `.jpg`/`.jpeg` extension

## Filename Generation (for saving received images)

**Format:** `{timestamp}-input.{ext}`
- Timestamp: `yyyy-mm-dd-hh-mm-ss` (24-hour)
- Extension: preserve original, default to `png` if unknown

Examples:
- `2025-11-23-14-23-05-input.png`
- `2025-11-23-15-30-12-input.jpg`

## Preflight + Common Failures

- Preflight:
  - `command -v uv` (must exist)
  - `test -f "/path/to/image.png"` (input must exist on disk)

- Common failures:
  - `Error: Input image not found:` → wrong path; verify `--image` points to a real file
  - `Error: --opacity must be between 0 and 255` → fix the opacity value
  - Output looks identical → spacing/thickness too small for image resolution; increase both

## Example

```bash
OUTPUT=$(uv run skills/grid-overlay/scripts/grid_overlay.py \
  --image "2025-11-23-14-23-05-input.png" \
  --spacing 40 \
  --thickness 4 \
  --opacity 200)

echo "Grid overlay saved to: $OUTPUT"
```
