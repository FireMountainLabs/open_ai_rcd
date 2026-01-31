# Service Architecture

AI_RCD is composed of three main architectural components.

## 1. Dashboard Service (Flask)
The user-facing web application that provides the visualization and management interface.

## 2. Database Service (FastAPI)
The internal API that provides high-speed access to the SQLite risk and control data.

## 3. Data Processing Service (Python)
An offline processing service that transforms raw Excel source documents into the normalized SQLite database used by the other services.
