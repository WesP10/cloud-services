# RPi Hub Cloud Service

FastAPI cloud service for testing rpi-hub-service WebSocket communication.

FastAPI is responsible for establishing both REST API and WebSocket endpoints on the cloud backend. 


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
      Extracts username and password from the request sent by the client (json or form)
      Logs that it has received the credentials and authenticates it
      logs error for error in username
      otherwise, generates a JWT token 
- `GET /auth/me` - Get current user info
      returns current user's username, email ID, and full name

### Hubs
Manages connected hardware hubs
Reads device state from the memory store.
A physical hub device must have already connected to your server and registered itself into the memory store.


- `GET /api/hubs` - List connected hubs
      An authenticated client requests the list

- `GET /api/hubs/{hubId}` - Get hub details
      if the hub doesnt exist, it raises an error.

- `GET /api/hubs/{hubId}/telemetry` - Get telemetry data
- `POST /api/hubs/{hubId}/commands/write` - Send serial write command
   A hub is essentially a device with multiple ports, where each port represents a physical connection point (like a serial port). Commands are sent to a port on a hub, and telemetry data is recorded from a port on a hub.

- `POST /api/hubs/{hubId}/commands/flash` - Send flash firmware command
- `POST /api/hubs/{hubId}/commands/restart` - Send restart device command

### WebSocket
- `WS /hub` - Hub connection endpoint (device token auth)

   Client endpoint: 
      manages browser/client WebSocket connections to the backend
      Each connected browser gets a ClientConnection
      they're subscribed to (which hub+port combinations they want live data from)

   hub endpoint: 
      manages hub websocket connections to the backend
      
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
   uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
   ```

## Mock Users

- Username: `admin`, Password: `<your password>`
- Username: `developer`, Password: `<your password>`
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
   uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
   ```

## Mock Users

- Username: `admin`, Password: `<your password>`
- Username: `developer`, Password: `<your password>`
