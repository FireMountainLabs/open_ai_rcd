# AI_RCD Troubleshooting Guide

Common issues and their solutions.

## Services Won't Start
- Check if ports 5001 or 5002 are in use.
- Run `./launch_dataviewer --logs` to see error output.

## Database Generation Fails
- Ensure all Excel files are present in `source_docs/`.
- Check `data-processing-service/config/default_config.yaml` for correct column mappings.

## UI Data is Missing
- Ensure `aiml_data.db` was generated successfully.
- Verify the Database Service is healthy: `curl http://localhost:5001/api/health`.
