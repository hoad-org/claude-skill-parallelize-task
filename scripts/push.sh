#!/bin/bash
# Push Docker image to registry
# Usage: ./scripts/push.sh [tag] [registry]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION=$(grep '^version = ' "$PROJECT_ROOT/pyproject.toml" | head -1 | cut -d'"' -f2)
TAG="${1:-$VERSION}"
REGISTRY="${2:-docker.io}"
IMAGE_NAME="parallelizer"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"
LATEST_IMAGE="${REGISTRY}/${IMAGE_NAME}:latest"

echo "=================================="
echo "Pushing Docker Image"
echo "=================================="
echo "Image: $FULL_IMAGE"
echo "Latest: $LATEST_IMAGE"
echo ""

# Check if image exists locally
if ! docker inspect "$FULL_IMAGE" &>/dev/null; then
  echo "❌ Image not found: $FULL_IMAGE"
  echo "Build the image first: ./scripts/build.sh $TAG $REGISTRY"
  exit 1
fi

# Check Docker credentials
echo "🔐 Verifying Docker credentials..."
if ! docker auth 2>/dev/null || ! docker info &>/dev/null; then
  echo "❌ Not logged in to Docker registry"
  echo "Run: docker login $REGISTRY"
  exit 1
fi

# Push the specific version
echo "📤 Pushing $FULL_IMAGE..."
docker push "$FULL_IMAGE" || {
  echo "❌ Failed to push $FULL_IMAGE"
  exit 1
}

# Push the latest tag
echo "📤 Pushing $LATEST_IMAGE..."
docker push "$LATEST_IMAGE" || {
  echo "⚠️  Failed to push latest tag (may already exist)"
}

echo ""
echo "✅ Push complete!"
echo ""
echo "Image available at:"
echo "  - $FULL_IMAGE"
echo "  - $LATEST_IMAGE"
echo ""
echo "Verify with:"
echo "  docker pull $FULL_IMAGE"
echo "  docker inspect $FULL_IMAGE"
