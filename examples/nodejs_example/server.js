/**
 * Node.js Express server example using DynaPort.
 * 
 * This example demonstrates how to use DynaPort with a Node.js Express application.
 * It uses the DynaPort CLI to allocate a port and register the service.
 */

const express = require('express');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

// Create Express app
const app = express();

// Add a simple health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    app_id: 'nodejs-express',
    instance_id: process.env.INSTANCE_ID || 'default'
  });
});

// Add a simple API endpoint
app.get('/api/data', (req, res) => {
  res.json({
    message: 'Hello from Node.js Express!',
    port: process.env.PORT,
    data: [
      { id: 1, name: 'Item 1' },
      { id: 2, name: 'Item 2' },
      { id: 3, name: 'Item 3' }
    ]
  });
});

// Add DynaPort info endpoint
app.get('/dynaport/info', (req, res) => {
  res.json({
    app_id: 'nodejs-express',
    instance_id: process.env.INSTANCE_ID || 'default',
    name: 'Node.js Express Example',
    port: process.env.PORT,
    technology: 'nodejs'
  });
});

// Main function to start the server
async function main() {
  try {
    // Get instance ID from command line or use default
    const instanceId = process.argv[2] || 'default';
    process.env.INSTANCE_ID = instanceId;
    
    // Use DynaPort CLI to allocate a port
    console.log(`Allocating port for nodejs-express (instance: ${instanceId})...`);
    const { stdout } = await execAsync(`dynaport port allocate nodejs-express --instance ${instanceId}`);
    
    // Extract the port from the output
    const portMatch = stdout.match(/PORT=(\d+)/);
    if (!portMatch) {
      throw new Error('Failed to allocate port');
    }
    
    const port = portMatch[1];
    process.env.PORT = port;
    console.log(`Allocated port ${port}`);
    
    // Register the service
    console.log('Registering service...');
    await execAsync(
      `dynaport service register nodejs-express ${port} ` +
      `--instance ${instanceId} ` +
      `--name "Node.js Express Example" ` +
      `--health-endpoint /health ` +
      `--technology nodejs ` +
      `--metadata '{"language":"javascript"}'`
    );
    
    // Start the server
    app.listen(port, () => {
      console.log(`Server running at http://localhost:${port}`);
      console.log('Press Ctrl+C to stop');
      
      // Update service status to running
      exec(`dynaport service status nodejs-express running --instance ${instanceId}`);
    });
    
    // Handle graceful shutdown
    process.on('SIGINT', async () => {
      console.log('\nShutting down...');
      
      try {
        // Update service status to stopped
        await execAsync(`dynaport service status nodejs-express stopped --instance ${instanceId}`);
        
        // Unregister the service
        await execAsync(`dynaport service unregister nodejs-express --instance ${instanceId}`);
        
        // Release the port
        await execAsync(`dynaport port release nodejs-express --instance ${instanceId}`);
        
        console.log('Cleanup complete');
        process.exit(0);
      } catch (error) {
        console.error('Error during cleanup:', error);
        process.exit(1);
      }
    });
  } catch (error) {
    console.error('Error:', error);
    process.exit(1);
  }
}

// Run the main function
main();
