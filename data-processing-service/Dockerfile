# Multi-stage optimized Dockerfile for Data Processing Service
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
FROM base as builder

# Install service-specific dependencies
COPY data-processing-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip cache purge

# Runtime stage - minimal production image
FROM base as runtime

# Copy installed packages from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code in optimal order for caching
# Copy configuration files first (least likely to change)
COPY --chown=appuser:appuser data-processing-service/config/ config/

# Copy Python application files
COPY --chown=appuser:appuser data-processing-service/app.py data-processing-service/data_processor.py data-processing-service/database_manager.py ./

# Copy utility modules
COPY --chown=appuser:appuser data-processing-service/utils/ utils/
COPY --chown=appuser:appuser data-processing-service/extractors/ extractors/

# Create service-specific directories
RUN mkdir -p /app/data /app/output /app/logs && \
    chown -R appuser:appuser /app

# Set service-specific environment variables
ENV DATA_DIR=/app/data
ENV OUTPUT_DIR=/app/output
ENV CONFIG_FILE=/app/config/default_config.yaml
ENV LOG_LEVEL=INFO
ENV VALIDATE_FILES=true
ENV REMOVE_DUPLICATES=true
ENV SERVICE_NAME=data-processing-service

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5002

# Optimized health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Use exec form for better signal handling
CMD ["python", "app.py"]

# Labels for metadata and optimization
LABEL maintainer="AI/ML Dashboard Team"
LABEL description="Optimized Data Processing Service for AI/ML Dashboard"
LABEL version="2.0.0"
LABEL service="data-processing"
LABEL org.opencontainers.image.source="https://github.com/firemountainlabs/dashboard_zero"
