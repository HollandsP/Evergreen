import type { NextApiRequest, NextApiResponse } from 'next';
import { Server as SocketIOServer } from 'socket.io';
import { Server as HttpServer } from 'http';

type ExtendedNextApiResponse = NextApiResponse & {
  socket: {
    server: HttpServer & {
      io?: SocketIOServer;
    };
  };
};

export default function handler(req: NextApiRequest, res: ExtendedNextApiResponse) {
  if (res.socket.server.io) {
    console.log('Socket.IO already initialized');
    return res.end();
  }

  console.log('Initializing Socket.IO server...');

  const io = new SocketIOServer(res.socket.server, {
    path: '/api/socket',
    cors: {
      origin: process.env.NODE_ENV === 'production' 
        ? process.env.NEXTAUTH_URL 
        : ['http://localhost:3000', 'http://127.0.0.1:3000'],
      methods: ['GET', 'POST'],
      credentials: true,
    },
    transports: ['websocket', 'polling'],
  });

  res.socket.server.io = io;

  io.on('connection', (socket) => {
    console.log('Client connected:', socket.id);

    // Handle job subscriptions
    socket.on('subscribe_job', ({ jobId }) => {
      console.log(`Client ${socket.id} subscribing to job ${jobId}`);
      socket.join(`job:${jobId}`);
    });

    socket.on('unsubscribe_job', ({ jobId }) => {
      console.log(`Client ${socket.id} unsubscribing from job ${jobId}`);
      socket.leave(`job:${jobId}`);
    });

    // Handle system subscriptions
    socket.on('subscribe_system', () => {
      console.log(`Client ${socket.id} subscribing to system updates`);
      socket.join('system');
    });

    socket.on('unsubscribe_system', () => {
      console.log(`Client ${socket.id} unsubscribing from system updates`);
      socket.leave('system');
    });

    socket.on('disconnect', (reason) => {
      console.log(`Client ${socket.id} disconnected:`, reason);
    });

    // Send initial connection confirmation
    socket.emit('connected', { 
      message: 'Connected to Evergreen AI pipeline',
      timestamp: new Date().toISOString(),
    });
  });

  // If you have a backend WebSocket server, you can connect to it here
  // and relay messages between your backend and frontend clients
  connectToBackendWebSocket(io);

  console.log('Socket.IO server initialized');
  return res.end();
}

function connectToBackendWebSocket(io: SocketIOServer) {
  // In a real implementation, you'd connect to your backend WebSocket
  // and relay messages. For now, we'll simulate periodic updates.
  
  const backendWsUrl = process.env.BACKEND_WS_URL;
  
  if (backendWsUrl) {
    try {
      // Example with a WebSocket client to your backend
      const WebSocket = require('ws');
      const ws = new WebSocket(backendWsUrl);

      ws.on('open', () => {
        console.log('Connected to backend WebSocket');
      });

      ws.on('message', (data: Buffer) => {
        try {
          const message = JSON.parse(data.toString());
          
          // Relay backend messages to appropriate frontend clients
          switch (message.type) {
            case 'job_update':
              io.to(`job:${message.jobId}`).emit('job_update', message.data);
              break;
            case 'step_update':
              io.to(`job:${message.jobId}`).emit('step_update', message.data);
              break;
            case 'job_completed':
              io.to(`job:${message.jobId}`).emit('job_completed', message.data);
              break;
            case 'job_failed':
              io.to(`job:${message.jobId}`).emit('job_failed', message.data);
              break;
            case 'system_status':
              io.to('system').emit('system_status', message.data);
              break;
          }
        } catch (error) {
          console.error('Error processing backend WebSocket message:', error);
        }
      });

      ws.on('error', (error: Error) => {
        console.error('Backend WebSocket error:', error);
      });

      ws.on('close', () => {
        console.log('Backend WebSocket connection closed');
        // Implement reconnection logic if needed
      });

    } catch (error) {
      console.error('Failed to connect to backend WebSocket:', error);
    }
  } else {
    // For demo purposes, simulate job updates
    simulateJobUpdates(io);
  }
}

function simulateJobUpdates(io: SocketIOServer) {
  // This is for demo purposes only
  // In a real implementation, updates would come from your backend
  
  setInterval(() => {
    // Simulate system status updates
    const systemStatus = {
      dalle3Available: Math.random() > 0.1,
      flux1Available: Math.random() > 0.1,
      runwayAvailable: Math.random() > 0.05,
      activeJobs: Math.floor(Math.random() * 5),
      queueLength: Math.floor(Math.random() * 10),
      systemLoad: Math.random() * 0.8,
    };

    io.to('system').emit('system_status', systemStatus);
  }, 30000); // Update every 30 seconds
}