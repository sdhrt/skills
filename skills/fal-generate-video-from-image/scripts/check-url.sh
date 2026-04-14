#!/bin/bash

# Check if a URL is publicly accessible by making a HEAD request.
# Usage: check_url <url>
# Returns 0 if successful (200 OK, image content type), 1 otherwise.

url="$1"

# Make a HEAD request to check accessibility and content type
response=$(curl --silent --head --write-out "%{http_code}" --output /dev/null -s --url "$url" -H "Accept: image/*")
http_code=$response

# Check HTTP status code
if [ "$http_code" -ne 200 ]; then
  echo "Error: URL not accessible. HTTP status code: $http_code"
  exit 1
fi

# Check Content-Type (basic check for image types)
content_type=$(curl --silent --head -s --url "$url" | grep -i "Content-Type:" | cut -d' ' -f2 | tr -d '\r')

if [[ "$content_type" =~ ^image/ ]]; then
  echo "URL is accessible and appears to be an image."
  exit 0
else
  echo "Error: URL is accessible but does not appear to be an image. Content-Type: $content_type"
  exit 1
fi
