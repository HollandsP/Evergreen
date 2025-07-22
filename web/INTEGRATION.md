# Web Interface Integration Guide

This guide explains how to integrate the web interface with your unified pipeline service.

## Backend Integration Requirements

### 1. REST API Endpoints

Your backend service should provide these endpoints:

#### POST /api/v1/generate
Start a new generation job.

**Request:**
```json
{
  "prompt": "A majestic mountain landscape at golden hour",
  "provider": "dalle3", // or "flux1"
  "settings": {
    "imageSize": "1024x1024",
    "videoDuration": 10,
    "quality": "high",
    "seed": 12345 // optional
  }
}
```

**Response:**
```json
{
  "id": "job_abc123",
  "prompt": "A majestic mountain landscape at golden hour",
  "provider": "dalle3",
  "status": "pending",
  "progress": 0,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "imageSize": "1024x1024",
    "videoDuration": 10,
    "quality": "high"
  }
}
```

#### GET /api/v1/jobs
List all jobs for the user.

**Response:**
```json
[
  {
    "id": "job_abc123",
    "prompt": "A majestic mountain landscape",
    "provider": "dalle3",
    "status": "completed",
    "progress": 100,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z",
    "image_url": "https://example.com/image.png",
    "video_url": "https://example.com/video.mp4",
    "cost": {
      "imageGeneration": 0.040,
      "videoGeneration": 0.095,
      "total": 0.135
    }
  }
]
```

#### GET /api/v1/jobs/{id}
Get details for a specific job.

#### DELETE /api/v1/jobs/{id}
Cancel a running job.

#### GET /api/v1/status
Get system status.

**Response:**
```json
{
  "dalle3_available": true,
  "flux1_available": true,
  "runway_available": true,
  "active_jobs": 2,
  "queue_length": 5,
  "system_load": 0.75
}
```

#### GET /api/v1/jobs/{id}/download/{type}
Download generated media files.
- `type`: "image" or "video"
- Returns binary file data

### 2. WebSocket Events

Your backend should send these WebSocket events:

#### job_update
Sent when job status or progress changes.

```json
{
  "type": "job_update",
  "jobId": "job_abc123",
  "data": {
    "id": "job_abc123",
    "status": "generating_image",
    "progress": 25,
    "updated_at": "2024-01-15T10:32:00Z"
  }
}
```

#### step_update
Sent when a pipeline step status changes.

```json
{
  "type": "step_update",
  "jobId": "job_abc123",
  "data": {
    "id": "image_generation",
    "name": "Image Generation",
    "status": "running",
    "progress": 60,
    "startTime": "2024-01-15T10:30:00Z"
  }
}
```

#### job_completed
Sent when a job completes successfully.

```json
{
  "type": "job_completed",
  "jobId": "job_abc123",
  "data": {
    "id": "job_abc123",
    "status": "completed",
    "progress": 100,
    "image_url": "https://example.com/image.png",
    "video_url": "https://example.com/video.mp4",
    "cost": {
      "imageGeneration": 0.040,
      "videoGeneration": 0.095,
      "total": 0.135
    }
  }
}
```

#### job_failed
Sent when a job fails.

```json
{
  "type": "job_failed",
  "jobId": "job_abc123",
  "data": {
    "id": "job_abc123",
    "status": "failed",
    "error": "Image generation failed: API quota exceeded"
  }
}
```

## Integration with Unified Pipeline Service

### Python FastAPI Example

Here's how to integrate with the unified pipeline service created earlier:

```python
# In your FastAPI backend
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Web interface URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import your unified pipeline service
from src.services.unified_pipeline_service import UnifiedPipelineService

pipeline_service = UnifiedPipelineService()

@app.post("/api/v1/generate")
async def create_generation(request: GenerationRequest):
    # Start generation using unified pipeline
    job = await pipeline_service.generate_video_clip(
        prompt=request.prompt,
        provider=request.provider,
        settings=request.settings
    )
    
    # Return job details
    return {
        "id": job.id,
        "prompt": job.prompt,
        "provider": job.provider,
        "status": job.status,
        "progress": job.progress,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "metadata": job.metadata
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Subscribe to pipeline events
    async def send_updates():
        async for event in pipeline_service.get_events():
            await websocket.send_text(json.dumps({
                "type": event.type,
                "jobId": event.job_id,
                "data": event.data
            }))
    
    # Run update sender
    await send_updates()
```

### Environment Configuration

Set these environment variables for the web interface:

```bash
# Backend API URL
BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# WebSocket URL
NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws

# Optional: Authentication
API_TOKEN=your-api-token
```

### WebSocket Client Subscription

The web interface will automatically:

1. Connect to WebSocket on page load
2. Subscribe to job updates when starting generation
3. Update UI in real-time based on events
4. Handle reconnection on connection loss

### File Storage Integration

For media file downloads, ensure your backend:

1. Stores generated files in accessible location
2. Provides secure download URLs
3. Handles file cleanup after download
4. Supports both image and video formats

### Error Handling

The web interface expects these error formats:

```json
{
  "error": "Descriptive error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

## Testing Integration

### 1. Backend Health Check
```bash
curl http://localhost:8000/health
```

### 2. WebSocket Connection
```javascript
// In browser console
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => console.log(JSON.parse(event.data));
```

### 3. Generate Test Request
```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Test image",
    "provider": "dalle3",
    "settings": {
      "imageSize": "1024x1024",
      "videoDuration": 10,
      "quality": "high"
    }
  }'
```

## Deployment Considerations

### Production Setup

1. **SSL/TLS**: Use HTTPS for API and WSS for WebSocket
2. **Authentication**: Implement proper API authentication
3. **Rate Limiting**: Add rate limiting to prevent abuse
4. **File Storage**: Use cloud storage (AWS S3, etc.) for generated files
5. **CDN**: Use CDN for serving static files and media

### Security

1. **Input Validation**: Validate all inputs on backend
2. **File Security**: Scan uploaded/generated files
3. **CORS**: Configure proper CORS policies
4. **API Keys**: Secure API key management
5. **User Sessions**: Implement proper session management

### Monitoring

1. **Health Checks**: Implement comprehensive health checks
2. **Metrics**: Track generation success rates and timing
3. **Logging**: Log all API requests and errors
4. **Alerts**: Set up alerts for service failures

This integration guide ensures seamless communication between the web interface and your unified pipeline service, providing users with a responsive and reliable video generation experience.