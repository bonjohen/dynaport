# DynaPort Node.js Example

This example demonstrates how to use DynaPort with a Node.js Express application.

## Prerequisites

- Node.js 14 or higher
- npm
- DynaPort installed and available in your PATH

## Installation

```bash
npm install
```

## Usage

### Start the server

```bash
npm start
```

This will:
1. Use DynaPort to allocate a port
2. Register the service with DynaPort
3. Start the Express server on the allocated port
4. Update the service status to "running"

### Start multiple instances

You can start multiple instances of the server:

```bash
# Start instance1
npm run start:instance1

# In another terminal, start instance2
npm run start:instance2
```

### Stopping the server

Press Ctrl+C to stop the server. This will:
1. Update the service status to "stopped"
2. Unregister the service from DynaPort
3. Release the allocated port

## API Endpoints

- `GET /health` - Health check endpoint
- `GET /api/data` - Example API endpoint
- `GET /dynaport/info` - DynaPort information endpoint

## How it works

This example uses the DynaPort CLI to:
1. Allocate a port using `dynaport port allocate`
2. Register the service using `dynaport service register`
3. Update the service status using `dynaport service status`
4. Unregister the service using `dynaport service unregister`
5. Release the port using `dynaport port release`

The Express server is configured to use the allocated port and provide the necessary endpoints for DynaPort integration.
