# Multi-stage optimized Dockerfile for Database Service
# Minimizes image size and maximizes caching efficiency

# Build base image first
FROM python:3.9-slim as base
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

# Build stage - install service-specific dependencies
FROM base AS builder

# Switch to root for package installation
USER root

# Install service-specific dependencies
COPY database-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage - minimal production image
FROM base AS runtime

# Copy installed packages from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code in optimal order for caching
# Copy configuration files first (least likely to change)
COPY --chown=appuser:appuser database-service/config.yaml ./

# Copy Python application files
COPY --chown=appuser:appuser database-service/app.py database-service/config_manager.py ./
COPY --chown=appuser:appuser database-service/api ./api
COPY --chown=appuser:appuser database-service/db ./db

# Create data directory with proper permissions
RUN mkdir -p /data && chown -R appuser:appuser /data

# Set service-specific environment variables
ENV DB_PATH=/data/aiml_data.db
ENV SERVICE_NAME=database-service

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${DATABASE_PORT}

# Optimized health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${DATABASE_PORT}/api/health || exit 1

# Use exec form for better signal handling
CMD ["python", "app.py"]

# Labels for metadata and optimization
LABEL maintainer="AI/ML Dashboard Team"
LABEL description="Optimized Database Service for AI/ML Dashboard"
LABEL version="2.0.0"
LABEL service="database"
LABEL org.opencontainers.image.source="https://github.com/firemountainlabs/dashboard_zero"
