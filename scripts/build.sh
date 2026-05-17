#!/bin/bash
# Build Docker image with versioning and tagging
# Usage: ./scripts/build.sh [tag] [registry]

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION=$(grep '^version = ' "$PROJECT_ROOT/pyproject.toml" | head -1 | cut -d'"' -f2)
TAG="${1:-$VERSION}"
REGISTRY="${2:-docker.io}"
IMAGE_NAME="parallelizer"
FULL_IMAGE="${REGISTRY}/${IMAGE_NAME}:${TAG}"

echo "=================================="
echo "Building Docker Image"
echo "=================================="
echo "Version: $VERSION"
echo "Tag: $TAG"
echo "Image: $FULL_IMAGE"
echo "Registry: $REGISTRY"
echo ""

# Verify Dockerfile exists
if [ ! -f "$PROJECT_ROOT/Dockerfile" ]; then
  echo "❌ Dockerfile not found at $PROJECT_ROOT/Dockerfile"
  exit 1
fi

# Verify pyproject.toml exists
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
  echo "❌ pyproject.toml not found at $PROJECT_ROOT/pyproject.toml"
  exit 1
fi

# Build the image
echo "📦 Building image: $FULL_IMAGE"
cd "$PROJECT_ROOT"

docker build \
  --file Dockerfile \
  --tag "$FULL_IMAGE" \
  --tag "${REGISTRY}/${IMAGE_NAME}:latest" \
  --build-arg VERSION="$VERSION" \
  --label "org.opencontainers.image.version=$VERSION" \
  --label "org.opencontainers.image.url=https://github.com/anthropics/claude-skill-parallelize-task" \
  --label "org.opencontainers.image.source=https://github.com/anthropics/claude-skill-parallelize-task" \
  --label "org.opencontainers.image.vendor=Anthropic" \
  . || {
  echo "❌ Docker build failed"
  exit 1
}

echo ""
echo "✅ Build complete!"
echo ""
echo "Image details:"
docker inspect "$FULL_IMAGE" --format='
  Repository: {{index .RepoTags 0}}
  Architecture: {{.Architecture}}
  OS: {{.Os}}
  Size: {{.Size}} bytes
  Created: {{.Created}}
' || true

echo ""
echo "Next steps:"
echo "  1. Test the image: docker run --rm $FULL_IMAGE --help"
echo "  2. Push the image: ./scripts/push.sh $TAG $REGISTRY"
echo "  3. Deploy to Kubernetes: ./scripts/deploy.sh $TAG"
