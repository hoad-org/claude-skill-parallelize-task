# Multi-stage Dockerfile for claude-skill-parallelize-task
# Stage 1: Builder - compile dependencies and prepare environment
FROM python:3.12-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Build the wheel
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels .

# Stage 2: Runtime - minimal production image
FROM python:3.12-slim

# Metadata
LABEL maintainer="Claude Code <claude@anthropic.com>"
LABEL description="Claude Skill: Parallelizer Task - Intelligent task parallelization and orchestration"
LABEL version="1.1.0"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src:$PYTHONPATH

# Create non-root user for security
RUN useradd -m -u 1000 -s /sbin/nologin parallelizer && \
    mkdir -p /app /app/data /app/logs && \
    chown -R parallelizer:parallelizer /app

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /build/wheels /wheels

# Install the application and runtime dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --no-index --find-links=/wheels /wheels/* && \
    rm -rf /wheels

# Copy application code
COPY --chown=parallelizer:parallelizer src/ ./src/
COPY --chown=parallelizer:parallelizer docs/ ./docs/

# Create data and logs directories
RUN mkdir -p /app/data /app/logs && \
    chown -R parallelizer:parallelizer /app/data /app/logs

# Switch to non-root user
USER parallelizer

# Health check - verify the CLI is functional
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose monitoring/metrics port
EXPOSE 8000 9090

# Default command - run the CLI with help (can be overridden)
CMD ["parallelize-task", "--help"]
