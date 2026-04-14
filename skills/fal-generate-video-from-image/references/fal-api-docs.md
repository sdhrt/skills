# Fal.ai API Documentation for Seedance 2.0 Image-to-Video

This document provides essential details for interacting with the fal.ai Seedance 2.0 Image-to-Video model via their queue API.

## Endpoint

- **Queue API:** `https://queue.fal.run/bytedance/seedance-2.0/image-to-video`

## Authentication

- API requests require an Authorization header with your Fal API key:
  `Authorization: Key YOUR_FAL_API_KEY` (or `FAL_KEY`)

## Request Parameters

The API accepts a JSON payload with the following parameters:

### Required Parameters

- **`prompt`** (`string`):
  A text description of the desired motion and action for the video.
  - *Example:* "A construction man managing traffic with supercars and hypercars cruising around"

- **`image_url`** (`string`):
  The URL of the starting frame image to animate. Must be a publicly accessible HTTPS URL or a Data URI. Supported formats: JPEG, PNG, WebP. Max 30 MB.
  - *Example:* `"https://media.istockphoto.com/id/1388637792/photo/rearview-shot-of-a-traffic-warden-guiding-vehicles-outdoors.jpg?s=612x612&w=0&k=20&c=j76t1Qo3fJIC8QHFDNi0FnTvMbDGe7nsALz6f4aMYoQ="`

### Optional Parameters

- **`resolution`** (`string`): Video resolution. Options: `"480p"`, `"720p"`. Default: `"720p"`.
- **`duration`** (`string`): Duration of the video in seconds. Options: `"4"` to `"15"`, or `"auto"`. Default: `"auto"`.
- **`aspect_ratio`** (`string`): Aspect ratio of the video. Options: `"auto"`, `"21:9"`, `"16:9"`, `"4:3"`, `"1:1"`, `"3:4"`, `"9:16"`. Default: `"auto"`.
- **`generate_audio`** (`boolean`): Whether to generate synchronized audio. Default: `true`.

## Response Schema

The API returns a JSON object that includes:

- **`request_id`** (`string`): Unique identifier for the request.
- **`status`** (`string`): Current status (e.g., `IN_QUEUE`, `IN_PROGRESS`, `COMPLETED`, `FAILED`).
- **`response_url`** (`string`): A URL to fetch the final result (e.g., video URL) once the status is `COMPLETED`.
- **`status_url`** (`string`): A URL to poll for the latest status of the request.
- **`video`** (`object`, if COMPLETED): Contains details of the generated video, including `url`.

## Polling for Completion

After submitting a request, poll the `status_url` to check progress. The skill will poll every minute for up to 10 minutes, or until the status is `COMPLETED`.

## Security

- API keys should be kept confidential and preferably loaded from environment variables.
- Image URLs must be publicly accessible HTTPS URLs or Data URIs. Local `file://` URLs are not supported by the remote service.
