---
name: fal-image-upload
description: Convert a local image file to a base64 data URI suitable for use as image_url in fal.ai API calls. No external dependencies required.
---

## Purpose

Takes a local image file path and outputs a base64-encoded data URI string (`data:<mime>;base64,...`) that can be used as `image_url` when calling fal.ai model endpoints. This avoids the need for a publicly hosted URL or the `fal-client` Python package.

## Triggers

- A local image file needs to be passed to a fal.ai model endpoint as `image_url`.
- The `fal-generate-video-from-image` skill (or similar) needs an `image_url` but only a local file path is available.
- Any situation where `file://` protocol won't work and no public URL exists for a local image.

## Constraints

- **Image files only.** Supported types: `png`, `jpg`/`jpeg`, `gif`, `webp`, `bmp`, `tiff`/`tif`, `svg`. If the file is not one of these types, reject with a clear error and stop.
- **File size warning.** Data URIs embed the entire file in the request payload. Files larger than 10 MB will work but will be slow. Files larger than 20 MB should be rejected with advice to use `fal-client` CDN upload instead.
- **No external dependencies.** Only `base64`, `file`, and standard shell utilities are required.

## Workflow

1. **Input:** A local file path (absolute or relative).

2. **Validate the file exists:**
   ```bash
   if [ ! -f "$FILE_PATH" ]; then
     echo "Error: File not found: $FILE_PATH"
     exit 1
   fi
   ```

3. **Detect MIME type and validate it is an image:**
   ```bash
   MIME_TYPE=$(file --mime-type -b "$FILE_PATH")
   if [[ ! "$MIME_TYPE" =~ ^image/ ]]; then
     echo "Error: Not an image file. Detected MIME type: $MIME_TYPE"
     exit 1
   fi
   ```

4. **Check file size:**
   ```bash
   # Cross-platform file size
   if [[ "$(uname)" == "Darwin" ]]; then
     FILE_SIZE=$(stat -f%z "$FILE_PATH")
   else
     FILE_SIZE=$(stat -c%s "$FILE_PATH")
   fi

   MAX_SIZE=$((20 * 1024 * 1024))
   WARN_SIZE=$((10 * 1024 * 1024))

   if [ "$FILE_SIZE" -gt "$MAX_SIZE" ]; then
     echo "Error: File is $(( FILE_SIZE / 1024 / 1024 )) MB. Data URI approach is not suitable for files over 20 MB. Use fal-client CDN upload (pip install fal-client) instead."
     exit 1
   fi

   if [ "$FILE_SIZE" -gt "$WARN_SIZE" ]; then
     echo "Warning: File is $(( FILE_SIZE / 1024 / 1024 )) MB. The request payload will be large and may be slow."
   fi
   ```

5. **Encode to base64 (cross-platform):**
   ```bash
   if [[ "$(uname)" == "Darwin" ]]; then
     BASE64_DATA=$(base64 -i "$FILE_PATH")
   else
     BASE64_DATA=$(base64 -w 0 "$FILE_PATH")
   fi
   ```

6. **Construct the data URI:**
   ```bash
   DATA_URI="data:${MIME_TYPE};base64,${BASE64_DATA}"
   ```

7. **Output:** The `DATA_URI` string. This is the value to use as `image_url` in fal.ai API calls.

## Output Format

The output is a single string in the format:

```
data:<mime_type>;base64,<base64_encoded_data>
```

Example:
```
data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...
```

## Usage by Other Skills

When the `fal-generate-video-from-image` skill (or any skill that calls fal.ai) needs an `image_url` from a local file:

1. Run this skill's workflow to get the `DATA_URI` value.
2. Use that value directly as the `image_url` parameter in the API call.

**Important:** The `check-url.sh` script in `fal-generate-video-from-image` does not handle `data:` URIs. When `image_url` is a data URI (starts with `data:`), the URL pre-check step must be skipped. The calling skill should check for the `data:` prefix and bypass `check-url.sh` accordingly.

## Limitations

- Data URIs inflate the JSON request payload significantly. For a 5 MB image, the base64 encoding adds ~33%, making the payload ~6.7 MB.
- Some fal.ai models may have request size limits that reject very large payloads. If this happens, the only alternative is CDN upload via `fal-client`.
- This skill does not produce a reusable URL. Each API call carries the full image data. If the same image is used across multiple calls, each call re-transmits the full payload.

## File Structure

```
.claude/skills/fal-image-upload/
└── SKILL.md
```
