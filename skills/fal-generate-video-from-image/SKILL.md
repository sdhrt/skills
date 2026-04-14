---
name: fal-generate-video-from-image
description: Create a video from an image using fal ai. This is asynchronous, after request has been submitted, we need to poll for getting the generation status.
---

## Purpose
Creates videos using fal.ai's seedance-2.0 image-to-video model via the queue endpoint. It performs a pre-check for image URL accessibility, submits the request, polls for status updates, and returns the CDN URL upon completion.

## Triggers
- Requests to create videos from images using fal.ai.
- Mentions of fal.ai, seedance-2.0, image-to-video generation.

## Tools Needed
- `curl` for making API requests to fal.ai (queue and status endpoints).
- `cron` for status polling.

## Workflow

1.  **Input:** `image_url`, `prompt`.
    - If `image_url` is a local file path (not a URL), first run the `fal-image-upload` skill (located at `skills/fal-image-upload/SKILL.md`) to convert it to a data URI. Use the resulting data URI string as `image_url`.

2.  **URL Pre-check:**
    - If `image_url` starts with `data:image/`, skip this pre-check entirely — data URIs do not need URL accessibility validation.
    - Otherwise, uses `/scripts/check-url.sh` to verify if `image_url` is publicly accessible and returns a valid image content type (e.g., `image/jpeg`, `image/png`).
    - If not accessible or not an image, returns a clear error message and stops.

3.  **API Request (via curl):**
    - If URL is accessible, calls the fal.ai queue endpoint: `https://queue.fal.run/bytedance/seedance-2.0/image-to-video`.
    - **Parameters:**
        - `prompt`: User-provided.
        - `image_url`: User-provided (must be public HTTPS or Data URI).
        - `resolution`: "720p" (default)
        - `duration`: "6" (default)
        - `aspect_ratio`: "9:16" (portrait, default)
        - `generate_audio`: `false` (default)
    - **Authentication:** Reads `FAL_API_KEY` from environment variables.

4.  **Polling for Status:**
    - If the initial API request returns `IN_QUEUE` and provides `status_url` and `response_url`:
        - Sets up a cron job to poll the `status_url` every minute for a maximum of 10 minutes.
        - The cron job will check the `status`.

5.  **Output:**
    - If `COMPLETED`: Fetches the video URL from the `response_url` and share it.
    - If `FAILED` or timeout: Reports the error or timeout to the user.

## File Structure

```
skills/fal-ai-video-curl/
├── SKILL.md
├── references/
│   └── fal-api-docs.md
└── scripts/
    └── check-url.sh
```

## API Key Configuration
The FAL API key should be set as an environment variable named `FAL_API_KEY` or `FAL_KEY`.

## Notes
- This skill assumes `curl` and `cron` are available in the execution environment.
- The `file://` protocol is not suitable for remote API calls; public HTTPS URLs or Data URIs are required for `image_url`.
- Error handling for API rate limits or unexpected fal.ai responses is basic and can be expanded.
