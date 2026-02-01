# AI_RCD Deployment Guide

This guide describes how to deploy the AI Risks, Controls, and Definitions Viewer in various environments.

## Local Deployment

### 1. Pre-flight Checks
Before starting, ensure your system meets the minimum requirements:
- **Docker**: Engine 20.10+ and Compose V2.
- **Resources**: 2GB+ free RAM and 1GB disk space.
- **Network**: Ports `5001` (API) and `5002` (UI) must be available.

### 2. Prepare Environment
The system uses `config/common.yaml` for default port mappings and settings. If you need to override these (e.g., if ports 5001/5002 are in use), create a `.env` file in the root:
```bash
DATABASE_PORT=5001
DASHBOARD_PORT=5002
LOG_LEVEL=INFO
```

### 3. Build & Generate Database
The platform is powered by a normalized SQLite database generated from local Excel files.
```bash
# Build the images
docker compose build

# Generate 'aiml_data.db' from 'source_docs/*.xlsx'
docker compose run --rm data-processing-service
```
> [!NOTE]
> You must run the database generation step whenever you update the Excel files in `source_docs/`.

### 4. Start Services
```bash
# Start in detached mode
docker compose up -d

# Verify health
docker compose ps
```
The dashboard will be available at [http://localhost:5002](http://localhost:5002).

## Production Considerations

### Backend Security
The application does not include built-in SSL or advanced authentication. For production:
- **Reverse Proxy**: Use Nginx or HAProxy to handle TLS/SSL termination.
- **Auth**: Implement OIDC or basic auth at the proxy level if exposing to the internet.

### Data Persistence
Ensure `aiml_data.db` is included in your backup rotation. While the database is read-only for the API services, it is the single source of truth for the viewer.

## Troubleshooting

- **"Port already in use"**: Change the port mapping in `.env` and restart.
- **"Database not found"**: Ensure step 3 was completed successfully and `aiml_data.db` exists in the root directory.
- **"Container unhealthy"**: Check logs with `docker compose logs [service-name]` to see startup errors.
