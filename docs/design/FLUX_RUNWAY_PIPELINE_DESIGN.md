# Flux.1 + RunwayML Interactive Pipeline Design

## System Architecture Overview

### Core Components

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Web Interface (React/Next.js)                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐  │
│  │  Flux.1 Prompt  │    │ Workflow Visual  │    │  Video Player   │  │
│  │     Editor      │    │   Dashboard      │    │    & Preview    │  │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘  │
│                                                                         │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐  │
│  │ Pipeline Config │    │ Progress Tracker │    │  Export Options │  │
│  │    Controls     │    │   & WebSocket    │    │   & Download    │  │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐  │
│  │   Flux.1 API    │    │  RunwayML API    │    │ ElevenLabs API  │  │
│  │   Integration   │    │   (gen4_turbo)   │    │  Integration    │  │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘  │
│                                                                         │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐  │
│  │ Celery Worker   │    │ Redis Queue      │    │ PostgreSQL DB   │  │
│  │    Manager      │    │ & Progress Cache │    │  & S3 Storage   │  │
│  └─────────────────┘    └──────────────────┘    └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 1. Web Interface Design

### 1.1 Main Dashboard Layout

```
┌────────────────────────────────────────────────────────────────────┐
│                        AI Video Generation Studio                   │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Image Generation (Flux.1)                 │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │ Prompt:                                                      │  │
│  │ ┌───────────────────────────────────────────────────────┐  │  │
│  │ │ A cinematic shot of a futuristic city at sunset...    │  │  │
│  │ └───────────────────────────────────────────────────────┘  │  │
│  │                                                             │  │
│  │ [Advanced Settings ▼]  Style: [Photorealistic ▼]           │  │
│  │                        Resolution: [1280x720 ▼]            │  │
│  │                                                             │  │
│  │                    [Generate Image]                         │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Workflow Visualization                     │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │                                                               │  │
│  │  [Text] ──► [Flux.1] ──► [Image] ──► [Runway] ──► [Video]  │  │
│  │    │          ⚡          ✓ Done      🔄 Processing         │  │
│  │    │                                                         │  │
│  │    └──► [ElevenLabs] ──► [Audio] ──► [Assembly] ──► [MP4]  │  │
│  │            ⏳ Waiting                                        │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    Generated Content                          │  │
│  ├─────────────────────────────────────────────────────────────┤  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐           │  │
│  │  │   Image    │  │   Video    │  │   Audio    │           │  │
│  │  │  Preview   │  │  Preview   │  │  Waveform  │           │  │
│  │  └────────────┘  └────────────┘  └────────────┘           │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Specifications

#### Image Generation Component
```typescript
interface ImageGenerationProps {
  onImageGenerated: (imageUrl: string) => void;
  defaultPrompt?: string;
}

interface FluxSettings {
  model: "flux.1-pro" | "flux.1-dev";
  steps: number;
  guidance: number;
  seed?: number;
  style: "photorealistic" | "artistic" | "anime" | "3d";
  resolution: "1280x720" | "1920x1080" | "720x1280";
}
```

#### Progress Tracking Component
```typescript
interface WorkflowStep {
  id: string;
  name: string;
  status: "pending" | "processing" | "completed" | "failed";
  progress?: number;
  startTime?: Date;
  endTime?: Date;
  output?: {
    url: string;
    type: "image" | "video" | "audio";
  };
}
```

## 2. API Design

### 2.1 Flux.1 Integration Service

```python
class FluxImageGenerator:
    """Flux.1 API integration for image generation"""
    
    def __init__(self):
        self.api_key = os.getenv('FLUX_API_KEY')
        self.base_url = "https://api.flux.ai/v1"
        
    async def generate_image(
        self,
        prompt: str,
        style: str = "photorealistic",
        resolution: str = "1280x720",
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate image with Flux.1"""
        
        # Enhance prompt based on style
        enhanced_prompt = self._enhance_prompt(prompt, style)
        
        payload = {
            "prompt": enhanced_prompt,
            "model": "flux.1-pro",
            "width": int(resolution.split('x')[0]),
            "height": int(resolution.split('x')[1]),
            "num_inference_steps": 50,
            "guidance_scale": 7.5,
            "seed": seed or random.randint(0, 1000000)
        }
        
        response = await self._make_request(payload)
        return {
            "image_url": response["url"],
            "seed": response["seed"],
            "prompt_used": enhanced_prompt
        }
    
    def _enhance_prompt(self, prompt: str, style: str) -> str:
        """Enhance prompt based on selected style"""
        style_modifiers = {
            "photorealistic": "photorealistic, high detail, 4k, cinematic lighting",
            "artistic": "artistic, painterly, expressive brushstrokes",
            "anime": "anime style, cel shaded, vibrant colors",
            "3d": "3d rendered, octane render, volumetric lighting"
        }
        return f"{prompt}, {style_modifiers.get(style, '')}"
```

### 2.2 Pipeline Orchestration API

```python
@router.post("/generate/clip")
async def generate_clip(
    request: ClipGenerationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate a single video clip with full pipeline"""
    
    # Create pipeline job
    job = PipelineJob(
        id=str(uuid4()),
        status="pending",
        workflow_steps=[
            {"id": "flux_image", "name": "Image Generation", "status": "pending"},
            {"id": "runway_video", "name": "Video Generation", "status": "pending"},
            {"id": "elevenlabs_audio", "name": "Audio Generation", "status": "pending"},
            {"id": "assembly", "name": "Media Assembly", "status": "pending"}
        ]
    )
    
    # Queue async processing
    background_tasks.add_task(process_clip_pipeline, job.id, request)
    
    return {
        "job_id": job.id,
        "websocket_url": f"/ws/progress/{job.id}",
        "status": "queued"
    }
```

### 2.3 WebSocket Progress Updates

```python
@router.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    """Real-time progress updates via WebSocket"""
    await websocket.accept()
    
    try:
        while True:
            # Get job status from Redis
            status = await redis_client.get(f"job:{job_id}")
            
            if status:
                await websocket.send_json({
                    "type": "progress",
                    "data": json.loads(status)
                })
                
                if status["status"] in ["completed", "failed"]:
                    break
            
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        pass
```

## 3. Pipeline Processing Flow

### 3.1 Complete Clip Generation Pipeline

```python
async def process_clip_pipeline(job_id: str, request: ClipGenerationRequest):
    """Process complete pipeline for single clip"""
    
    try:
        # Step 1: Generate image with Flux.1
        await update_job_status(job_id, "flux_image", "processing")
        
        flux = FluxImageGenerator()
        image_result = await flux.generate_image(
            prompt=request.image_prompt,
            style=request.style,
            resolution=request.resolution
        )
        
        await update_job_status(job_id, "flux_image", "completed", {
            "image_url": image_result["image_url"]
        })
        
        # Step 2: Generate video with RunwayML
        await update_job_status(job_id, "runway_video", "processing")
        
        runway = RunwayMLProperClient()
        video_prompt = request.video_prompt or self._generate_video_prompt(
            request.image_prompt
        )
        
        task = runway.generate_video_from_image(
            image_url=image_result["image_url"],
            prompt=video_prompt,
            duration=request.duration,
            model="gen4_turbo"
        )
        
        video_url = await runway.wait_for_completion_async(task["id"])
        
        await update_job_status(job_id, "runway_video", "completed", {
            "video_url": video_url
        })
        
        # Step 3: Generate audio if script provided
        if request.audio_script:
            await update_job_status(job_id, "elevenlabs_audio", "processing")
            
            audio_url = await generate_audio(
                text=request.audio_script,
                voice_id=request.voice_id
            )
            
            await update_job_status(job_id, "elevenlabs_audio", "completed", {
                "audio_url": audio_url
            })
        
        # Step 4: Assemble final video
        await update_job_status(job_id, "assembly", "processing")
        
        final_video = await assemble_media(
            video_url=video_url,
            audio_url=audio_url if request.audio_script else None
        )
        
        await update_job_status(job_id, "assembly", "completed", {
            "final_video_url": final_video
        })
        
    except Exception as e:
        await update_job_status(job_id, "error", "failed", {
            "error": str(e)
        })
```

## 4. Frontend Implementation

### 4.1 React Components Structure

```typescript
// Main App Component
const VideoGenerationStudio: React.FC = () => {
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [workflowSteps, setWorkflowSteps] = useState<WorkflowStep[]>([]);
  
  const handleGenerateClip = async (config: ClipConfig) => {
    const response = await api.generateClip(config);
    setCurrentJob(response);
    
    // Connect WebSocket for progress
    const ws = new WebSocket(response.websocket_url);
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setWorkflowSteps(update.workflow_steps);
    };
  };
  
  return (
    <div className="studio-container">
      <ImageGenerator onGenerate={handleGenerateClip} />
      <WorkflowVisualizer steps={workflowSteps} />
      <MediaPreview job={currentJob} />
      <PipelineControls />
    </div>
  );
};
```

### 4.2 Workflow Visualization Component

```typescript
const WorkflowVisualizer: React.FC<{steps: WorkflowStep[]}> = ({steps}) => {
  return (
    <div className="workflow-container">
      {steps.map((step, index) => (
        <div key={step.id} className="workflow-step">
          <StepIcon status={step.status} />
          <div className="step-details">
            <h4>{step.name}</h4>
            {step.status === "processing" && (
              <ProgressBar progress={step.progress || 0} />
            )}
            {step.status === "completed" && step.output && (
              <PreviewThumbnail url={step.output.url} type={step.output.type} />
            )}
          </div>
          {index < steps.length - 1 && <Arrow />}
        </div>
      ))}
    </div>
  );
};
```

## 5. Automated Video Assembly

### 5.1 Full Pipeline Assembly System

```python
class VideoAssemblyPipeline:
    """Automated assembly of all clips and audio into final video"""
    
    async def assemble_full_video(
        self,
        project_id: str,
        clips: List[Dict[str, str]]
    ) -> str:
        """
        Assemble complete video from clips and audio tracks
        
        Args:
            project_id: Project identifier
            clips: List of clip configs with video_url, audio_url, duration
        
        Returns:
            URL of final assembled video
        """
        
        # Download all media files
        video_files = []
        audio_files = []
        
        for i, clip in enumerate(clips):
            video_path = await self._download_file(
                clip["video_url"], 
                f"clip_{i}.mp4"
            )
            video_files.append(video_path)
            
            if clip.get("audio_url"):
                audio_path = await self._download_file(
                    clip["audio_url"],
                    f"audio_{i}.mp3"
                )
                audio_files.append(audio_path)
        
        # Create FFmpeg command for assembly
        output_path = f"output/{project_id}_final.mp4"
        
        ffmpeg_cmd = self._build_ffmpeg_command(
            video_files,
            audio_files,
            output_path
        )
        
        # Execute assembly
        await self._run_ffmpeg(ffmpeg_cmd)
        
        # Upload to S3
        final_url = await self._upload_to_s3(output_path, project_id)
        
        return final_url
    
    def _build_ffmpeg_command(
        self,
        videos: List[str],
        audios: List[str],
        output: str
    ) -> List[str]:
        """Build FFmpeg command for assembly"""
        
        # Create concat file
        concat_file = "concat_list.txt"
        with open(concat_file, "w") as f:
            for video in videos:
                f.write(f"file '{video}'\n")
        
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output
        ]
        
        return cmd
```

## 6. Database Schema

```sql
-- Pipeline jobs table
CREATE TABLE pipeline_jobs (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    status VARCHAR(50) NOT NULL,
    workflow_config JSONB,
    workflow_steps JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);

-- Generated media table
CREATE TABLE generated_media (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES pipeline_jobs(id),
    media_type VARCHAR(20) NOT NULL, -- 'image', 'video', 'audio'
    url VARCHAR(500) NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Clip configurations table
CREATE TABLE clip_configs (
    id UUID PRIMARY KEY,
    project_id UUID REFERENCES projects(id),
    sequence_number INTEGER NOT NULL,
    image_prompt TEXT,
    video_prompt TEXT,
    audio_script TEXT,
    voice_id VARCHAR(100),
    duration INTEGER DEFAULT 10,
    style VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 7. Configuration Management

### 7.1 Pipeline Settings Interface

```typescript
interface PipelineSettings {
  flux: {
    model: "flux.1-pro" | "flux.1-dev";
    defaultStyle: string;
    defaultResolution: string;
    apiKey?: string; // User's own key
  };
  runway: {
    model: "gen4_turbo" | "gen3a_turbo";
    defaultDuration: number;
    contentModeration: {
      publicFigureThreshold: "auto" | "low";
    };
    apiKey?: string;
  };
  elevenlabs: {
    defaultVoice: string;
    stability: number;
    similarityBoost: number;
    apiKey?: string;
  };
  assembly: {
    outputFormat: "mp4" | "mov" | "webm";
    quality: "low" | "medium" | "high";
    includeWatermark: boolean;
  };
}
```

### 7.2 User Preferences Storage

```python
class UserPreferences:
    """Store and manage user pipeline preferences"""
    
    def save_preferences(self, user_id: str, prefs: Dict[str, Any]):
        """Save user preferences to database"""
        
    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """Retrieve user preferences"""
        
    def apply_to_pipeline(self, pipeline: Pipeline, user_id: str):
        """Apply user preferences to pipeline configuration"""
```

## 8. Example RunwayML Prompts (for your review)

### Photorealistic Style
```
Prompt: "Aerial establishing shot of modern city skyline at golden hour, 
documentary cinematography, smooth drone movement, photorealistic quality, 
natural lighting with long shadows, 4K clarity, cinematic depth of field"

Cost: ~$0.50 (10 seconds)
```

### Cinematic Style
```
Prompt: "Character walking through rain-soaked street at night, noir 
cinematography style, tracking shot following subject, neon reflections 
on wet pavement, shallow depth of field, moody atmospheric lighting"

Cost: ~$0.50 (10 seconds)
```

### Dynamic Action
```
Prompt: "Fast-paced montage of city life, quick cuts between scenes, 
dynamic camera movements, time-lapse elements, urban energy and motion, 
documentary style capture of daily life"

Cost: ~$0.50 (10 seconds)
```

## 9. Cost Optimization

### 9.1 Credit Management
- Track usage per user/project
- Set spending limits
- Cache generated content
- Reuse common elements

### 9.2 Preview Mode
- Generate 5-second previews first
- Low-resolution test generations
- Watermarked samples for approval

## 10. Security Considerations

### 10.1 API Key Management
- Encrypted storage for user API keys
- Option to use platform keys with billing
- Rate limiting per user
- Audit logging for all generations

### 10.2 Content Moderation
- Pre-flight prompt checking
- NSFW content filtering
- Copyright detection for prompts
- User content reporting system

---

This design provides a complete interactive pipeline that:
1. Lets users control each step of generation
2. Shows real-time progress with visual workflow
3. Allows prompt editing and style customization
4. Integrates Flux.1 for images → RunwayML for video
5. Includes ElevenLabs for audio generation
6. Automates final assembly of all media
7. Provides cost tracking and optimization

Would you like me to start implementing any specific component of this system?