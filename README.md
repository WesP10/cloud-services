# RPi Hub Cloud Service

FastAPI cloud service for testing rpi-hub-service WebSocket communication.

## Features

- WebSocket hub connection endpoint (`/hub`)
- JWT authentication for API endpoints
- Device token authentication for hub connections
- In-memory storage for testing
- REST API for triggering commands and viewing telemetry
- Full bidirectional messaging with hub service

## Quick Start

### Installation

```bash
cd cloud-services
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your settings
```

### Run Server

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

Server will be available at `http://localhost:8080`

API documentation at `http://localhost:8080/docs`

## API Endpoints

### Authentication
- `POST /auth/login` - Login with username/password, get JWT token
- `GET /auth/me` - Get current user info

### Hubs
- `GET /api/hubs` - List connected hubs
- `GET /api/hubs/{hubId}` - Get hub details
- `GET /api/hubs/{hubId}/telemetry` - Get telemetry data
- `POST /api/hubs/{hubId}/commands/write` - Send serial write command
- `POST /api/hubs/{hubId}/commands/flash` - Send flash firmware command
- `POST /api/hubs/{hubId}/commands/restart` - Send restart device command

### WebSocket
- `WS /hub` - Hub connection endpoint (device token auth)

## Testing with rpi-hub-service

1. Start this cloud service:
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
   ```

2. Configure rpi-hub-service `.env`:
   ```env
   SERVER_ENDPOINT=ws://localhost:8080/hub
   DEVICE_TOKEN=dev-token-rpi-bridge-01
   ```

3. Start rpi-hub-service:
   ```bash
   cd ../rpi-hub-service
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```

## Mock Users

- Username: `admin`, Password: `admin123`
- Username: `developer`, Password: `dev123`
