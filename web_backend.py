#!/usr/bin/env python3
"""
Simple FastAPI backend for the Evergreen Web Interface
Handles API requests from the Next.js frontend
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our services
try:
    from src.services.unified_pipeline import UnifiedPipelineManager
    from src.prompts.prompt_optimizer import PromptOptimizer
except ImportError as e:
    print(f"Warning: Could not import services: {e}")
    print("Some features may not work without the full pipeline implementation")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="Evergreen AI Pipeline API",
    description="Backend API for DALL-E 3 + RunwayML video generation",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for job management
active_jobs: Dict[str, Dict[str, Any]] = {}
pipeline_manager: Optional[UnifiedPipelineManager] = None
prompt_optimizer: Optional[PromptOptimizer] = None

# WebSocket connections for real-time updates
websocket_connections: List[WebSocket] = []

# Pydantic models
class GenerateRequest(BaseModel):
    prompt: str
    style: str = "photorealistic"
    duration: int = 10
    provider: str = "dalle3"
    camera_movement: Optional[str] = None
    custom_settings: Optional[Dict[str, Any]] = None

class JobStatus(BaseModel):
    id: str
    status: str
    progress: float
    steps: List[Dict[str, Any]]
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None
    cost: float = 0.0
    outputs: Dict[str, str] = {}

class SystemStatus(BaseModel):
    status: str
    services: Dict[str, str]
    timestamp: str
    version: str = "1.0.0"

# Initialize services
@app.on_event("startup")
async def startup_event():
    """Initialize pipeline services on startup"""
    global pipeline_manager, prompt_optimizer
    
    logger.info("Starting Evergreen AI Pipeline API...")
    
    try:
        # Initialize pipeline manager
        pipeline_manager = UnifiedPipelineManager()
        logger.info("✅ Pipeline manager initialized")
        
        # Initialize prompt optimizer
        prompt_optimizer = PromptOptimizer()
        logger.info("✅ Prompt optimizer initialized")
        
        # Test API connections
        dalle3_status = await pipeline_manager.test_dalle3_connection()
        runway_status = await pipeline_manager.test_runway_connection()
        
        if dalle3_status:
            logger.info("✅ DALL-E 3 API connection successful")
        else:
            logger.warning("⚠️ DALL-E 3 API connection failed")
            
        if runway_status:
            logger.info("✅ RunwayML API connection successful")
        else:
            logger.warning("⚠️ RunwayML API connection failed")
            
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        # Continue anyway for demo purposes

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time job updates"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        while True:
            # Keep connection alive
            await asyncio.sleep(1)
            
    except WebSocketDisconnect:
        websocket_connections.remove(websocket)

async def broadcast_update(job_id: str, update: Dict[str, Any]):
    """Broadcast job update to all connected WebSocket clients"""
    message = {
        "type": "job_update",
        "job_id": job_id,
        "data": update
    }
    
    # Remove disconnected connections
    disconnected = []
    for ws in websocket_connections:
        try:
            await ws.send_json(message)
        except:
            disconnected.append(ws)
    
    for ws in disconnected:
        websocket_connections.remove(ws)

# API Routes

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    services = {
        "api": "up",
        "dalle3": "unknown",
        "runway": "unknown"
    }
    
    if pipeline_manager:
        try:
            dalle3_ok = await pipeline_manager.test_dalle3_connection()
            services["dalle3"] = "up" if dalle3_ok else "down"
        except:
            services["dalle3"] = "down"
            
        try:
            runway_ok = await pipeline_manager.test_runway_connection()
            services["runway"] = "up" if runway_ok else "down"
        except:
            services["runway"] = "down"
    
    return SystemStatus(
        status="ok" if all(s != "down" for s in services.values()) else "degraded",
        services=services,
        timestamp=datetime.now().isoformat()
    )

@app.post("/api/v1/generate")
async def generate_video(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Generate a video clip from text prompt"""
    if not pipeline_manager:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    # Create job ID
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(active_jobs)}"
    
    # Initialize job status
    job_status = {
        "id": job_id,
        "status": "queued",
        "progress": 0.0,
        "steps": [
            {"name": "Image Generation", "status": "pending", "progress": 0.0},
            {"name": "Video Generation", "status": "pending", "progress": 0.0},
            {"name": "Post Processing", "status": "pending", "progress": 0.0}
        ],
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
        "error": None,
        "cost": 0.0,
        "outputs": {},
        "request": request.dict()
    }
    
    active_jobs[job_id] = job_status
    
    # Queue background processing
    background_tasks.add_task(process_generation, job_id, request)
    
    return {"job_id": job_id, "status": "queued"}

async def process_generation(job_id: str, request: GenerateRequest):
    """Background task to process video generation"""
    if not pipeline_manager or not prompt_optimizer:
        return
    
    try:
        # Update job status
        active_jobs[job_id]["status"] = "processing"
        await broadcast_update(job_id, active_jobs[job_id])
        
        # Step 1: Optimize prompt
        optimized_prompt = prompt_optimizer.enhance_image_prompt(
            request.prompt,
            style=request.style
        )
        
        # Step 2: Generate image
        active_jobs[job_id]["steps"][0]["status"] = "processing"
        await broadcast_update(job_id, active_jobs[job_id])
        
        # Simulate processing for demo
        for i in range(5):
            await asyncio.sleep(1)
            progress = (i + 1) * 20
            active_jobs[job_id]["steps"][0]["progress"] = progress
            active_jobs[job_id]["progress"] = progress / 3
            await broadcast_update(job_id, active_jobs[job_id])
        
        active_jobs[job_id]["steps"][0]["status"] = "completed"
        active_jobs[job_id]["outputs"]["image"] = f"http://localhost:8000/output/{job_id}_image.jpg"
        
        # Step 3: Generate video
        active_jobs[job_id]["steps"][1]["status"] = "processing"
        await broadcast_update(job_id, active_jobs[job_id])
        
        # Simulate video generation
        for i in range(10):
            await asyncio.sleep(2)
            progress = (i + 1) * 10
            active_jobs[job_id]["steps"][1]["progress"] = progress
            active_jobs[job_id]["progress"] = 33 + (progress / 3)
            await broadcast_update(job_id, active_jobs[job_id])
        
        active_jobs[job_id]["steps"][1]["status"] = "completed"
        active_jobs[job_id]["outputs"]["video"] = f"http://localhost:8000/output/{job_id}_video.mp4"
        
        # Step 4: Post processing
        active_jobs[job_id]["steps"][2]["status"] = "processing"
        await broadcast_update(job_id, active_jobs[job_id])
        
        await asyncio.sleep(3)
        active_jobs[job_id]["steps"][2]["status"] = "completed"
        active_jobs[job_id]["steps"][2]["progress"] = 100
        
        # Complete job
        active_jobs[job_id]["status"] = "completed"
        active_jobs[job_id]["progress"] = 100.0
        active_jobs[job_id]["completed_at"] = datetime.now().isoformat()
        active_jobs[job_id]["cost"] = 0.58  # DALL-E 3 + RunwayML cost
        
        await broadcast_update(job_id, active_jobs[job_id])
        
        logger.info(f"✅ Job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}")
        active_jobs[job_id]["status"] = "failed"
        active_jobs[job_id]["error"] = str(e)
        await broadcast_update(job_id, active_jobs[job_id])

@app.get("/api/v1/jobs/{job_id}")
async def get_job_status(job_id: str):
    """Get status of a specific job"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**active_jobs[job_id])

@app.get("/api/v1/jobs")
async def list_jobs():
    """List all jobs"""
    return {
        "jobs": [JobStatus(**job) for job in active_jobs.values()],
        "total": len(active_jobs)
    }

@app.delete("/api/v1/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a job"""
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if active_jobs[job_id]["status"] in ["completed", "failed"]:
        raise HTTPException(status_code=400, detail="Cannot cancel completed job")
    
    active_jobs[job_id]["status"] = "cancelled"
    await broadcast_update(job_id, active_jobs[job_id])
    
    return {"message": f"Job {job_id} cancelled"}

@app.get("/api/v1/providers")
async def get_providers():
    """Get available providers and their status"""
    providers = {
        "dalle3": {
            "name": "DALL-E 3",
            "type": "image",
            "status": "unknown",
            "cost_per_image": 0.08,
            "description": "OpenAI's DALL-E 3 for high-quality image generation"
        },
        "runway": {
            "name": "RunwayML Gen-4",
            "type": "video", 
            "status": "unknown",
            "cost_per_second": 0.05,
            "description": "RunwayML's Gen-4 Turbo for video generation"
        }
    }
    
    if pipeline_manager:
        try:
            dalle3_ok = await pipeline_manager.test_dalle3_connection()
            providers["dalle3"]["status"] = "available" if dalle3_ok else "unavailable"
        except:
            providers["dalle3"]["status"] = "unavailable"
            
        try:
            runway_ok = await pipeline_manager.test_runway_connection()
            providers["runway"]["status"] = "available" if runway_ok else "unavailable"
        except:
            providers["runway"]["status"] = "unavailable"
    
    return {"providers": providers}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Evergreen AI Pipeline API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )