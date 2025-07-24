"""
WebSocket server for real-time updates.

Provides WebSocket endpoints for job progress, system status, and real-time notifications.
"""

import json
import asyncio
from typing import Dict, Set, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState
import structlog

logger = structlog.get_logger()


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, Set[str]] = {}  # topic -> set of connection_ids
        
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and track a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info("WebSocket client connected", client_id=client_id)
        
        # Send connection confirmation
        await self.send_personal_message({
            "type": "connected",
            "message": "Connected to Evergreen AI pipeline backend",
            "timestamp": datetime.now().isoformat()
        }, client_id)
        
    def disconnect(self, client_id: str):
        """Remove a WebSocket connection and clean up subscriptions."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
        # Remove from all subscriptions
        for topic, subscribers in self.subscriptions.items():
            subscribers.discard(client_id)
            
        logger.info("WebSocket client disconnected", client_id=client_id)
        
    async def send_personal_message(self, message: dict, client_id: str):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            if websocket.client_state == WebSocketState.CONNECTED:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error("Error sending message to client", 
                                client_id=client_id, error=str(e))
                    
    async def broadcast_to_topic(self, topic: str, message: dict):
        """Broadcast a message to all clients subscribed to a topic."""
        if topic in self.subscriptions:
            disconnected_clients = []
            
            for client_id in self.subscriptions[topic]:
                if client_id in self.active_connections:
                    websocket = self.active_connections[client_id]
                    if websocket.client_state == WebSocketState.CONNECTED:
                        try:
                            await websocket.send_json(message)
                        except Exception as e:
                            logger.error("Error broadcasting to client", 
                                        client_id=client_id, error=str(e))
                            disconnected_clients.append(client_id)
                    else:
                        disconnected_clients.append(client_id)
                        
            # Clean up disconnected clients
            for client_id in disconnected_clients:
                self.disconnect(client_id)
                
    def subscribe(self, client_id: str, topic: str):
        """Subscribe a client to a topic."""
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        self.subscriptions[topic].add(client_id)
        logger.info("Client subscribed to topic", client_id=client_id, topic=topic)
        
    def unsubscribe(self, client_id: str, topic: str):
        """Unsubscribe a client from a topic."""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(client_id)
            logger.info("Client unsubscribed from topic", client_id=client_id, topic=topic)
            
    async def send_job_update(self, job_id: str, status: str, progress: float, 
                            message: str, metadata: Optional[dict] = None):
        """Send a job update to all clients subscribed to that job."""
        await self.broadcast_to_topic(f"job:{job_id}", {
            "type": "job_update",
            "jobId": job_id,
            "data": {
                "status": status,
                "progress": progress,
                "message": message,
                "metadata": metadata or {},
                "timestamp": datetime.now().isoformat()
            }
        })
        
    async def send_step_update(self, job_id: str, step: str, status: str, 
                             progress: float, details: Optional[dict] = None):
        """Send a step update for a specific job."""
        await self.broadcast_to_topic(f"job:{job_id}", {
            "type": "step_update",
            "jobId": job_id,
            "data": {
                "step": step,
                "status": status,
                "progress": progress,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            }
        })
        
    async def send_job_completed(self, job_id: str, result: dict):
        """Send job completion notification."""
        await self.broadcast_to_topic(f"job:{job_id}", {
            "type": "job_completed",
            "jobId": job_id,
            "data": {
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        })
        
    async def send_job_failed(self, job_id: str, error: str, details: Optional[dict] = None):
        """Send job failure notification."""
        await self.broadcast_to_topic(f"job:{job_id}", {
            "type": "job_failed",
            "jobId": job_id,
            "data": {
                "error": error,
                "details": details or {},
                "timestamp": datetime.now().isoformat()
            }
        })
        
    async def send_system_status(self, status: dict):
        """Send system status update to all subscribed clients."""
        await self.broadcast_to_topic("system", {
            "type": "system_status",
            "data": status
        })


# Global connection manager instance
manager = ConnectionManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Main WebSocket endpoint handler."""
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive and process messages from client
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "subscribe_job":
                job_id = data.get("jobId")
                if job_id:
                    manager.subscribe(client_id, f"job:{job_id}")
                    await manager.send_personal_message({
                        "type": "subscribed",
                        "topic": f"job:{job_id}"
                    }, client_id)
                    
            elif message_type == "unsubscribe_job":
                job_id = data.get("jobId")
                if job_id:
                    manager.unsubscribe(client_id, f"job:{job_id}")
                    await manager.send_personal_message({
                        "type": "unsubscribed",
                        "topic": f"job:{job_id}"
                    }, client_id)
                    
            elif message_type == "subscribe_system":
                manager.subscribe(client_id, "system")
                await manager.send_personal_message({
                    "type": "subscribed",
                    "topic": "system"
                }, client_id)
                
            elif message_type == "unsubscribe_system":
                manager.unsubscribe(client_id, "system")
                await manager.send_personal_message({
                    "type": "unsubscribed",
                    "topic": "system"
                }, client_id)
                
            elif message_type == "ping":
                await manager.send_personal_message({
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                }, client_id)
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error("WebSocket error", client_id=client_id, error=str(e))
        manager.disconnect(client_id)


# Background task to send periodic system status updates
async def system_status_broadcaster():
    """Periodically broadcast system status updates."""
    while True:
        try:
            # Get system status (you can customize this based on your needs)
            status = {
                "dalle3Available": True,  # Check actual API availability
                "runwayAvailable": True,  # Check actual API availability
                "elevenLabsAvailable": True,  # Check actual API availability
                "activeJobs": len([s for s in manager.subscriptions.keys() if s.startswith("job:")]),
                "connectedClients": len(manager.active_connections),
                "timestamp": datetime.now().isoformat()
            }
            
            await manager.send_system_status(status)
            
        except Exception as e:
            logger.error("Error broadcasting system status", error=str(e))
            
        # Wait 30 seconds before next update
        await asyncio.sleep(30)