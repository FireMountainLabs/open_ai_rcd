# Base image for all microservices
# Provides common Python environment and dependencies
# Updated: 2024-01-XX - Triggering full CI pipeline build

FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user first
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create virtual environment with appuser ownership
RUN python -m venv /opt/venv && \
    chown -R appuser:appuser /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy and install base requirements
COPY requirements/base.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Create data directory with proper permissions
RUN mkdir -p /data && chown -R appuser:appuser /data

# Switch to non-root user
USER appuser

# Labels for metadata
LABEL maintainer="AI/ML Dashboard Team"
LABEL description="Base image for AI/ML Dashboard microservices"
LABEL version="1.0.0"
LABEL org.opencontainers.image.source="https://github.com/firemountainlabs/dashboard_zero"
