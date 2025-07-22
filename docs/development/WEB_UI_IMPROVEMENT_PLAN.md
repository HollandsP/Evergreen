# Web UI Improvement Plan - Complete Redesign

## Current Issues Identified

1. **Confusing Workflow**: "ImageGeneratorPanel" shows image providers but button says "Generate Video"
2. **No Clear Separation**: Image generation, video generation, and script processing are mixed together
3. **Connection Issues**: UI shows "connecting" but never actually connects (WebSocket issue)
4. **Missing Script Integration**: No way to upload "The Descent" script and auto-generate prompts
5. **Missing API Key Management**: Flux.1 needs API key configuration
6. **No Audio Integration**: ElevenLabs audio generation not accessible
7. **No Complete Workflow**: No way to go from script → clips → audio → final video

## Proposed Solution: Audio-First Production Pipeline

### Stage 1: Script Processing
- **Upload Script**: User uploads "The Descent" script (.txt file)
- **Auto Scene Detection**: Parse timestamps and scenes automatically  
- **Extract Narration**: Separate narration text from visual descriptions
- **Scene Preview**: Show all scenes with narration text for review/editing

### Stage 2: Audio Generation (FIRST - Sets Timing Foundation)
- **Script-to-Audio**: Convert narration text to speech using ElevenLabs
- **Voice Selection**: Choose voice (Winston Marek character)
- **Audio Preview**: Review generated audio tracks with timing
- **Audio Analysis**: Extract timing, beats, emotional peaks for visual sync
- **Waveform Timeline**: Visual representation for scene timing

### Stage 3: Image Generation (Audio-Informed)
- **Generate Option**: Use DALL-E 3 or Flux.1 to generate scene images
- **Upload Option**: Upload custom images for scenes  
- **Audio-Guided Prompts**: Enhance prompts based on audio timing and mood
- **Preview Gallery**: Review all generated/uploaded images with audio preview
- **Batch Processing**: Generate all scenes at once or individually

### Stage 4: Video Generation (Audio-Synchronized)
- **Image-to-Video**: Convert each image to video using RunwayML
- **Audio Sync**: Match video timing to narration segments
- **Lip-Sync Features**: Use RunwayML character performance for talking scenes
- **Audio-Guided Camera Work**: Camera movements follow speech patterns
- **Motion Prompts**: Customize movement based on audio emotional beats
- **Preview Player**: Review videos with synchronized audio

### Stage 5: Final Assembly
- **Timeline Editor**: Arrange clips in sequence (audio already synchronized)
- **Fine-tune Sync**: Adjust any timing issues
- **Audio Mixing**: Add background music, sound effects if desired
- **Export Options**: Generate final video file
- **Download/Share**: Access completed production

## Implementation Plan

### Phase 1: Core UI Restructure
1. **Fix WebSocket Connection** - Resolve "connecting" issue
2. **Create Multi-Stage Navigation** - Tab-based or wizard-style interface
3. **Separate Concerns** - Split into focused components per stage

### Phase 2: Script Processing Integration
1. **ScriptUpload Component** - Handle "The Descent" script upload
2. **SceneParser Service** - Extract scenes, timestamps, narration text
3. **NarrationExtractor** - Separate narration from visual descriptions
4. **Scene Manager** - Preview/edit scenes with timing information

### Phase 3: Audio-First Generation Components
1. **AudioGenerator Component** - ElevenLabs integration (PRIORITY)
2. **AudioAnalyzer Service** - Extract timing, beats, emotional markers
3. **WaveformVisualizer** - Show audio timeline for visual planning
4. **ImageGenerator Component** - Audio-informed image generation
5. **ImageToVideo Component** - Audio-synchronized video generation with lip-sync
6. **BatchProcessor** - Handle multiple scenes with audio timing

### Phase 4: API Key Management
1. **Settings Panel** - Manage all API keys (OpenAI, RunwayML, Flux.1, ElevenLabs)
2. **Provider Status** - Show availability and costs
3. **Usage Tracking** - Monitor credits and costs

### Phase 5: Production Pipeline
1. **Timeline Component** - Sequence management
2. **Assembly Service** - FFmpeg integration for final rendering
3. **Export Manager** - Handle downloads and sharing

## File Structure Changes

```
web/
├── components/
│   ├── stages/
│   │   ├── ScriptProcessor.tsx          # Stage 1: Script upload & parsing
│   │   ├── AudioGenerator.tsx           # Stage 2: Voice generation (FIRST)
│   │   ├── ImageGenerator.tsx           # Stage 3: Audio-informed images  
│   │   ├── VideoGenerator.tsx           # Stage 4: Audio-synced videos
│   │   └── FinalAssembly.tsx            # Stage 5: Timeline & export
│   ├── audio/
│   │   ├── WaveformVisualizer.tsx       # Audio waveform display
│   │   ├── AudioAnalyzer.tsx            # Extract timing/emotional markers
│   │   ├── VoiceSelector.tsx            # ElevenLabs voice options
│   │   └── AudioPreview.tsx             # Audio playback with timing
│   ├── video/
│   │   ├── LipSyncControls.tsx          # RunwayML character performance
│   │   ├── AudioSyncTimeline.tsx        # Video-audio synchronization
│   │   └── CameraWorkGuide.tsx          # Audio-guided camera movements
│   ├── shared/
│   │   ├── ProgressTracker.tsx          # Cross-stage progress
│   │   ├── ApiKeyManager.tsx            # API key configuration
│   │   ├── CostEstimator.tsx            # Cost tracking
│   │   └── ScenePreview.tsx             # Scene preview with audio
│   └── layout/
│       ├── StageNavigation.tsx          # Multi-stage navigation
│       └── ProductionDashboard.tsx      # Main dashboard
├── pages/
│   ├── production/
│   │   ├── index.tsx                    # Main production interface
│   │   ├── script.tsx                   # Script processing stage
│   │   ├── audio.tsx                    # Audio generation stage (STAGE 2)
│   │   ├── images.tsx                   # Audio-informed image generation
│   │   ├── videos.tsx                   # Audio-synced video generation
│   │   └── assembly.tsx                 # Final assembly stage
│   └── api/
│       ├── script/
│       │   ├── upload.ts                # Handle script uploads
│       │   ├── parse.ts                 # Parse scenes and extract narration
│       │   └── analyze.ts               # Extract timing information
│       ├── audio/
│       │   ├── generate.ts              # ElevenLabs audio generation
│       │   ├── analyze.ts               # Audio timing/emotion analysis
│       │   └── voices.ts                # Available voices API
│       ├── generation/
│       │   ├── images.ts                # Audio-informed image generation
│       │   ├── videos.ts                # Audio-synced video generation
│       │   └── lipsync.ts               # Character performance/lip-sync
│       └── assembly/
│           ├── timeline.ts              # Audio-based timeline management
│           └── export.ts                # Final video export with audio
└── lib/
    ├── script-parser.ts                 # Script parsing utilities
    ├── audio-analyzer.ts                # Audio timing/emotion analysis
    ├── scene-manager.ts                 # Audio-informed scene management
    ├── sync-manager.ts                  # Audio-video synchronization
    └── production-state.ts              # Global production state
```

## Cost Estimation Framework

### Per-Stage Costs:
- **Stage 2 (Images)**: $0.08 per image (DALL-E 3) or $0.10 (Flux.1)
- **Stage 3 (Videos)**: $0.50 per 10-second clip (RunwayML)
- **Stage 4 (Audio)**: $0.15 per minute (ElevenLabs)
- **Total for "The Descent" (8 scenes)**: ~$5-7 estimated

### Real-time Cost Tracking:
- Show costs as user progresses through stages
- Provider comparison (DALL-E 3 vs Flux.1)
- Budget warnings and recommendations

## Success Metrics

1. **Clear Workflow**: User can easily understand and navigate the production process
2. **Script Integration**: "The Descent" script uploads and auto-generates proper prompts
3. **Complete Pipeline**: Full script → video production works end-to-end
4. **Cost Transparency**: Users understand costs at each stage
5. **Quality Output**: Generated videos match "The Descent" narrative style
6. **No Connection Issues**: WebSocket and API connections work reliably

## Next Steps

1. **Fix WebSocket Connection** (immediate)
2. **Create Stage Navigation** (high priority)
3. **Implement Script Processor** (high priority) 
4. **Separate Image/Video Generation** (high priority)
5. **Add Audio Generation** (medium priority)
6. **Build Final Assembly** (medium priority)

This redesign transforms the interface from a simple "generate video" tool into a complete AI film production pipeline optimized for "The Descent" and similar narrative projects.