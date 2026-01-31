# AI_RCD Deployment Guide

This guide describes how to deploy the AI Risks, Controls, and Definitions Viewer.

## Local Deployment

1. **Prerequisites**: Docker and Docker Compose installed.
2. **Environment**: `cp sample.env .env`.
3. **Database**: `./launch_dataviewer --generate-db`.
4. **Run**: `./launch_dataviewer`.

## Production Considerations

- **Security**: Enable authentication behind a reverse proxy (Nginx).
- **Persistence**: Ensure `aiml_data.db` and `.capability-configs/` are backed up.
- **Scaling**: Services can be scaled using Docker Compose scale or Kubernetes.
