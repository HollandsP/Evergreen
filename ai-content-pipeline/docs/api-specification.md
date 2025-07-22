# API Specification
## AI Content Generation Pipeline API v1.0

**Base URL**: `https://api.contentpipeline.ai/v1`  
**Authentication**: Bearer token (JWT)

---

## 1. Authentication

### 1.1 Obtain Access Token
```http
POST /auth/token
Content-Type: application/json

{
  "client_id": "your_client_id",
  "client_secret": "your_client_secret",
  "grant_type": "client_credentials"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

## 2. Projects

### 2.1 Create Project
```http
POST /projects
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "LOG_0002_DESCENT",
  "series_id": "ai-2027-race",
  "metadata": {
    "episode": 2,
    "season": 1
  }
}
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "LOG_0002_DESCENT",
  "series_id": "ai-2027-race",
  "status": "created",
  "created_at": "2025-01-20T10:00:00Z"
}
```

### 2.2 Get Project Status
```http
GET /projects/{project_id}
Authorization: Bearer {token}
```

**Response**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "LOG_0002_DESCENT",
  "status": "processing",
  "progress": {
    "script": "completed",
    "voice": "in_progress",
    "visual": "pending",
    "assembly": "pending"
  },
  "estimated_completion": "2025-01-20T11:30:00Z"
}
```

---

## 3. Content Generation

### 3.1 Generate Video
```http
POST /generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "story_content": "markdown content here...",
  "settings": {
    "voice_profile": "winston_marek",
    "visual_style": "dystopian_cinematic",
    "duration_target": "5-8 minutes",
    "quality": "high",
    "terminal_effects": true
  }
}
```

**Response**:
```json
{
  "job_id": "job_123456",
  "status": "queued",
  "estimated_time": 5400,
  "queue_position": 3
}
```

### 3.2 Generate with File Upload
```http
POST /generate/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

story_file: [file content]
settings: {
  "voice_profile": "winston_marek",
  "visual_style": "dystopian_cinematic"
}
```

---

## 4. Script Operations

### 4.1 Parse Script
```http
POST /scripts/parse
Authorization: Bearer {token}
Content-Type: application/json

{
  "content": "# LOG_0002: THE DESCENT\n\n...",
  "options": {
    "include_timing": true,
    "segment_by_speaker": true
  }
}
```

**Response**:
```json
{
  "segments": [
    {
      "id": 1,
      "speaker": "WINSTON_MAREK",
      "text": "Day 47. Berlin Sector 7.",
      "start_time": 0.0,
      "duration": 3.2,
      "scene": "interior_bunker"
    }
  ],
  "total_duration": 420.5,
  "character_count": {
    "WINSTON_MAREK": 85,
    "SYSTEM": 15
  }
}
```

---

## 5. Voice Synthesis

### 5.1 Generate Voice
```http
POST /voice/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "text": "Day 47. Berlin Sector 7.",
  "voice_id": "winston_marek",
  "settings": {
    "stability": 0.7,
    "similarity_boost": 0.8,
    "style": "serious"
  }
}
```

**Response**:
```json
{
  "audio_url": "https://cdn.contentpipeline.ai/audio/abc123.mp3",
  "duration": 3.2,
  "format": "mp3",
  "sample_rate": 44100
}
```

### 5.2 List Available Voices
```http
GET /voice/profiles
Authorization: Bearer {token}
```

---

## 6. Visual Generation

### 6.1 Generate Scene
```http
POST /visual/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "prompt": "Rooftop view of dystopian Berlin, white uniforms",
  "style": "cinematic, high contrast",
  "duration": 5,
  "settings": {
    "resolution": "1920x1080",
    "fps": 30,
    "camera_movement": "slow_pan_right"
  }
}
```

**Response**:
```json
{
  "video_url": "https://cdn.contentpipeline.ai/video/xyz789.mp4",
  "duration": 5.0,
  "resolution": "1920x1080",
  "generation_time": 180
}
```

---

## 7. Media Assembly

### 7.1 Create Assembly Job
```http
POST /assembly/create
Authorization: Bearer {token}
Content-Type: application/json

{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "timeline": [
    {
      "type": "video",
      "asset_id": "video_001",
      "start": 0,
      "duration": 5
    },
    {
      "type": "audio",
      "asset_id": "audio_001",
      "start": 0,
      "duration": 3.2
    }
  ],
  "export_settings": {
    "format": "mp4",
    "resolution": "1920x1080",
    "bitrate": "8000k"
  }
}
```

---

## 8. Job Management

### 8.1 Get Job Status
```http
GET /jobs/{job_id}
Authorization: Bearer {token}
```

**Response**:
```json
{
  "job_id": "job_123456",
  "type": "video_generation",
  "status": "processing",
  "progress": 65,
  "started_at": "2025-01-20T10:00:00Z",
  "logs": [
    {
      "timestamp": "2025-01-20T10:01:00Z",
      "message": "Script parsing completed"
    }
  ]
}
```

### 8.2 Cancel Job
```http
DELETE /jobs/{job_id}
Authorization: Bearer {token}
```

---

## 9. Templates

### 9.1 List Templates
```http
GET /templates?type=visual
Authorization: Bearer {token}
```

**Response**:
```json
{
  "templates": [
    {
      "id": "dystopian_city",
      "name": "Dystopian City Scene",
      "type": "visual",
      "parameters": ["time_of_day", "weather", "population_density"]
    }
  ]
}
```

### 9.2 Apply Template
```http
POST /templates/apply
Authorization: Bearer {token}
Content-Type: application/json

{
  "template_id": "dystopian_city",
  "parameters": {
    "time_of_day": "sunset",
    "weather": "foggy",
    "population_density": "abandoned"
  }
}
```

---

## 10. Batch Operations

### 10.1 Batch Generate
```http
POST /batch/generate
Authorization: Bearer {token}
Content-Type: application/json

{
  "jobs": [
    {
      "story_file": "LOG_0002_DESCENT.md",
      "settings": {...}
    },
    {
      "story_file": "LOG_0003_AWAKENING.md",
      "settings": {...}
    }
  ],
  "priority": "normal"
}
```

---

## 11. Webhooks

### 11.1 Register Webhook
```http
POST /webhooks
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["job.completed", "job.failed"],
  "secret": "your_webhook_secret"
}
```

### 11.2 Webhook Payload
```json
{
  "event": "job.completed",
  "timestamp": "2025-01-20T11:30:00Z",
  "data": {
    "job_id": "job_123456",
    "project_id": "550e8400-e29b-41d4-a716-446655440000",
    "output_url": "https://cdn.contentpipeline.ai/final/video.mp4"
  },
  "signature": "sha256=..."
}
```

---

## 12. Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit exceeded",
    "details": {
      "limit": 100,
      "reset_at": "2025-01-20T12:00:00Z"
    }
  }
}
```

### Common Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | Invalid or missing authentication |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 400 | Invalid request parameters |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

---

## 13. Rate Limits

| Endpoint | Limit | Window |
|----------|-------|---------|
| /generate | 10 | per hour |
| /voice/generate | 100 | per hour |
| /visual/generate | 30 | per hour |
| Other endpoints | 1000 | per hour |

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642680000
```

---

## 14. SDK Examples

### Python
```python
from contentpipeline import Client

client = Client(api_key="your_api_key")

# Generate video
result = client.generate(
    story_file="stories/LOG_0002.md",
    voice_profile="winston_marek",
    visual_style="dystopian"
)

print(f"Video URL: {result.output_url}")
```

### JavaScript
```javascript
const ContentPipeline = require('contentpipeline-js');

const client = new ContentPipeline({ apiKey: 'your_api_key' });

async function generateVideo() {
  const result = await client.generate({
    storyFile: 'stories/LOG_0002.md',
    voiceProfile: 'winston_marek',
    visualStyle: 'dystopian'
  });
  
  console.log(`Video URL: ${result.outputUrl}`);
}
```

---

## 15. OpenAPI Specification

Full OpenAPI 3.0 specification available at:
- JSON: `https://api.contentpipeline.ai/v1/openapi.json`
- YAML: `https://api.contentpipeline.ai/v1/openapi.yaml`

Interactive documentation:
- Swagger UI: `https://api.contentpipeline.ai/docs`
- ReDoc: `https://api.contentpipeline.ai/redoc`