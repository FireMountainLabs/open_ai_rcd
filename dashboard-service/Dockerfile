# Single-stage Dockerfile for Dashboard Service
# Simplified to resolve build context issues

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

# Build from base stage
FROM base as runtime

# Switch to root for package installation
USER root

# Install service-specific dependencies
COPY dashboard-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code in optimal order for caching
# Copy configuration files first (least likely to change)
COPY --chown=appuser:appuser dashboard-service/config.yaml ./

# Copy shared services
COPY --chown=appuser:appuser shared-services/common_config.py ./common_config.py

# Copy Python application files
COPY --chown=appuser:appuser dashboard-service/app.py dashboard-service/config_manager.py ./

# Copy Python packages (auth, routes, utils)
COPY --chown=appuser:appuser dashboard-service/auth/ ./auth/
COPY --chown=appuser:appuser dashboard-service/routes/ ./routes/
COPY --chown=appuser:appuser dashboard-service/utils/ ./utils/

# Copy static assets (templates and static files) - use explicit approach
COPY --chown=appuser:appuser dashboard-service/templates/ ./templates/
COPY --chown=appuser:appuser dashboard-service/static/ ./static/

# Set service-specific environment variables
ENV SERVICE_NAME=dashboard-service

# Switch to non-root user
USER appuser

# Expose port (will be set by docker-compose)
EXPOSE ${PORT}

# Optimized health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Use exec form for better signal handling
CMD ["python", "app.py"]

# Labels for metadata and optimization
LABEL maintainer="AI/ML Dashboard Team"
LABEL description="Optimized Dashboard Service for AI/ML Dashboard"
LABEL version="2.0.0"
LABEL service="dashboard"
LABEL org.opencontainers.image.source="https://github.com/firemountainlabs/dashboard_zero"
