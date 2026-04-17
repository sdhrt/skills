---
name: fal-ai-video
description: Generate video from a still image using Seedance 2.0 (fal.ai). Use for image-to-video, animate image, make video from photo requests. Async two-step workflow: submit then poll for result. Supports Telegram image input.
---

# Seedance 2.0 Image-to-Video

Animate a still image into a cinematic video with synchronized audio using ByteDance's Seedance 2.0 via fal.ai.

## Workflow (two-step async)

This skill uses an asynchronous queue. There are two scripts:

1. **`submit_video.py`** — uploads the image, submits the job, prints a `request_id`
2. **`poll.py`** — checks status by `request_id`, returns the CDN video URL when complete. There is also fallback poll.sh if poll.py doesn't work

### Step 1: Save the input image (if received from Telegram or chat)

If the user sends an image in chat (e.g. Telegram), save it to disk first before calling the submit script. Save to the user's current working directory with a descriptive filename:

```bash
# Example: save the received image bytes to disk
# The agent must write the image data to a file at a known path
# Use a timestamped name to avoid collisions
SAVE_PATH="$(pwd)/yyyy-mm-dd-hh-mm-ss-input.png"
```

If the user provides a path to an existing file on disk, use that path directly — do not re-save.

### Step 2: Apply grid overlay

Invoke the `grid-overlay` skill on the saved image. The skill will first ask the user to confirm whether the image already has a grid overlay:

- **If the user says the image already has a grid overlay:** skip running the script and use the original saved image path as `IMAGE_PATH`.
- **If the grid overlay script is run:** capture the output path printed to stdout and use that as `IMAGE_PATH` for the submit step.

```bash
# If grid overlay was run:
IMAGE_PATH=$(uv run skills/grid-overlay/scripts/grid_overlay.py --image "/path/to/saved/image.png")

# If image already has a grid overlay:
IMAGE_PATH="/path/to/saved/image.png"
```

### Step 3: Submit the request

Run the submit script using the absolute path (do NOT cd to the skill directory first):
If uv doesn't exist, please install it using
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
REQUEST_ID=$(uv run skills/fal-ai-video/scripts/submit_video.py \
  --prompt "motion description" \
  --image "$IMAGE_PATH" \
  [--resolution 480p|720p] \
  [--duration auto|4-15] \
  [--api-key KEY])
```

The `request_id` is printed to stdout. Informational messages go to stderr.

**Important:** Capture the `request_id` — it is required to retrieve the result.

### Step 4: Get the result

Poll for the result using the request_id:

```bash
VIDEO_URL=$(uv run skills/fal-ai-video/scripts/poll.py \
  --request-id "$REQUEST_ID" \
  [--api-key KEY])
```

```bash
./skills/fal-ai-video/scripts/poll.sh --request-id "$REQUEST_ID"
```

Exit codes:
- `0` — completed, video CDN URL printed to stdout
- `1` — error (auth, network, unexpected status)
- `2` — not ready yet (IN_QUEUE or IN_PROGRESS), try again later

### Polling strategy

Video generation takes 1–5 minutes depending on duration and resolution. Do not poll in a tight loop.

- First check: wait **60 seconds** after submit before first poll
- Subsequent checks: wait **30 seconds** between polls
- Maximum attempts: **15** (roughly 8 minutes total)
- If still not complete after max attempts, inform the user the job is still running and provide the `request_id` so they can check later

```bash
# Example polling loop
sleep 60
for i in $(seq 1 15); do
  VIDEO_URL=$(uv run skills/fal-ai-video/scripts/poll.py --request-id "$REQUEST_ID" 2>/dev/null)
  if [ $? -eq 0 ]; then
    echo "Video ready: $VIDEO_URL"
    break
  fi
  sleep 30
done
```

## Handling Telegram / Chat Images

When the user sends an image through Telegram (or any chat interface), the agent receives the image data or a local file path. The agent must:

1. Determine where the image data is (file path, base64 data, or binary blob)
2. Save it to disk as a PNG or JPEG file if not already on disk
3. Use the saved file path as the `--image` argument to `submit_video.py`

The submit script handles uploading the local file to fal.ai CDN internally — the agent only needs to provide a valid local file path.

## Parameters

### Required
- **`--prompt`** (`-p`): Describes the desired motion and action. Be specific about movement, camera angles, and transitions.
- **`--image`** (`-i`): Local path to the input image file. Supported formats: JPEG, PNG, WebP.

### Optional
- **`--resolution`** (`-r`): `480p` (faster) or `720p` (default, better quality)
- **`--duration`** (`-d`): `auto` (default, model decides) or `4` through `15` (seconds)
- **`--api-key`** (`-k`): fal.ai API key (overrides `FAL_KEY` env var)

## Resolution Mapping

Map user requests to the `--resolution` parameter:
- No mention of resolution → `720p`
- "low resolution", "fast", "quick", "draft" → `480p`
- "high resolution", "high quality", "720p" → `720p`

## Duration Mapping

Map user requests to the `--duration` parameter:
- No mention of duration → `auto`
- "short", "quick clip", "brief" → `4` or `5`
- "medium" → `8` or `10`
- "long", "extended" → `12` to `15`
- Specific number of seconds → use directly if between 4–15

## API Key

The scripts check for API key in this order:
1. `--api-key` argument (use if user provided key in chat)
2. `FAL_KEY` environment variable

If neither is available, the script exits with an error message.

## Preflight + Common Failures

- Preflight:
  - `command -v uv` (must exist)
  - `test -n "$FAL_KEY"` (or pass `--api-key`)
  - `test -f "/path/to/image.png"` (input image must exist on disk)

- Common failures:
  - `Error: No API key provided.` → set `FAL_KEY` or pass `--api-key`
  - `Error: Input image not found:` → wrong path; verify `--image` points to a real file
  - `Error uploading image:` → network issue or invalid file format
  - `Error submitting request:` → auth failure, quota, or API issue
  - Exit code `2` from poll → job not finished yet, poll again
  - HTTP 401/403 from result script → wrong API key or expired

## Filename Generation (for saving received images)

When saving an image received from chat, generate filenames with this pattern:

**Format:** `{timestamp}-input.{ext}`
- Timestamp: `yyyy-mm-dd-hh-mm-ss` (24-hour format)
- Extension: preserve original format, default to `png` if unknown

Examples:
- `2025-11-23-14-23-05-input.png`
- `2025-11-23-15-30-12-input.jpg`

## Prompt Handling

Pass the user's motion description as-is to `--prompt`. Only rework if clearly insufficient.

Good prompts describe **motion and action**, not static appearance (the image already provides that).

Examples of good prompts:
- "The woman slowly turns her head and smiles at the camera"
- "Waves crash against the rocks as the camera slowly zooms out"
- "The cat stretches and yawns, then jumps off the table"

Examples of bad prompts (too static):
- "A beautiful sunset" → rework to: "The sun slowly sets below the horizon, colors shifting from orange to deep purple"
- "A portrait of a man" → rework to: "The man blinks and subtly nods, with a slight breeze moving his hair"

## Output

- `submit_video.py` prints the `request_id` to stdout
- `poll.py` prints the video CDN URL to stdout when complete
- Share the CDN URL directly with the user — it is publicly accessible
- Do not attempt to download the video unless the user asks

## Examples

**Submit a video request:**
```bash
REQUEST_ID=$(uv run skills/fal-ai-video/scripts/submit_video.py \
  --prompt "The cat slowly turns its head and blinks" \
  --image "2025-11-23-14-23-05-input.png" \
  --resolution 720p \
  --duration auto)
```

**Check result:**
```bash
VIDEO_URL=$(uv run skills/fal-ai-video/scripts/poll.py \
  --request-id "$REQUEST_ID")
```

**Full flow with polling:**
```bash
REQUEST_ID=$(uv run skills/fal-ai-video/scripts/submit_video.py \
  --prompt "The flower blooms in timelapse as morning light shifts across it" \
  --image "photo.jpg")

echo "Submitted. Waiting for result..."
sleep 60

for i in $(seq 1 15); do
  VIDEO_URL=$(uv run skills/fal-ai-video/scripts/poll.py \
    --request-id "$REQUEST_ID" 2>/dev/null)
  if [ $? -eq 0 ]; then
    echo "Video ready: $VIDEO_URL"
    break
  fi
  echo "Not ready yet, waiting 30s... (attempt $i/15)"
  sleep 30
done
```
