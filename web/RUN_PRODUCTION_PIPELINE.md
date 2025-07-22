# 🚀 Running the Evergreen Production Pipeline

Since all API keys are already configured in the project environment, you can start using the production pipeline immediately!

## Quick Start

```bash
# Navigate to the web directory
cd /mnt/c/Users/holla/OneDrive/Desktop/CodeProjects/Evergreen/web

# Install dependencies (if not already done)
npm install

# Start the development server
npm run dev
```

## Access the Production Pipeline

1. Open your browser to: **http://localhost:3000/production**
2. You'll be redirected to the Script Processing stage

## Production Workflow

### Stage 1: Script Processing
- Click "Choose File" or drag & drop `ScriptLog0002TheDescent.txt`
- The script is located at: `/scripts/ScriptLog0002TheDescent.txt`
- Review the parsed scenes and narration
- Edit any narration text if needed
- Click "Continue to Audio Generation"

### Stage 2: Audio Generation (Audio-First)
- Select voice: "Winston - Calm" (recommended for the character)
- Click "Generate All Audio" to create narration for all scenes
- Wait for audio generation (uses ElevenLabs API)
- Preview audio with the built-in player
- Click "Continue to Image Generation"

### Stage 3: Image Generation
- Review auto-generated prompts for each scene
- All images use DALL-E 3 (Flux.1 removed due to cost)
- Click "Generate All Images" 
- Wait for image generation (~30-60 seconds per image)
- Upload custom images if desired
- Click "Continue to Video Generation"

### Stage 4: Video Generation
- Review video prompts and settings
- Lip-sync automatically enabled for dialogue scenes
- Adjust camera movements and motion intensity if desired
- Click "Generate All Videos"
- Preview videos with synchronized audio
- Click "Continue to Final Assembly"

### Stage 5: Final Assembly
- Review the timeline with all clips
- Drag to reorder scenes if needed
- Select transitions between clips
- Optionally add background music
- Configure export settings:
  - Format: MP4 (recommended)
  - Resolution: 1080p
  - Quality: High
- Click "Export Video"
- Download your final production!

## Cost Estimates

Based on "The Descent" (8 scenes):
- **Audio**: ~$0.30 (ElevenLabs - ~45 seconds total)
- **Images**: ~$0.32 (DALL-E 3 - 8 images @ $0.04 each)
- **Videos**: ~$4.00 (RunwayML - 8 clips @ ~$0.50 each)
- **Total**: ~$4.62 per complete video

## Tips for Success

1. **Script Format**: Ensure your script follows the LOG format:
   ```
   [0:00 - Scene Type | Description]
   Narration (Character):
   "Dialogue text here"
   ```

2. **Audio Quality**: The "male_calm" voice works best for Winston's character

3. **Image Prompts**: The system auto-generates cinematic prompts, but you can edit them for better results

4. **Lip-Sync**: Automatically enabled for scenes with dialogue - no manual configuration needed

5. **Export Time**: Final assembly may take 2-5 minutes depending on video length

## Troubleshooting

### WebSocket Connection Issues
- The connection status indicator should show "Connected" in green
- If it shows "Disconnected", refresh the page

### API Errors
- **Rate Limits**: Wait a few seconds between operations
- **Content Policy**: Modify prompts if DALL-E 3 rejects them
- **Timeouts**: Longer videos may take time - be patient

### Missing Data
- Each stage saves to localStorage
- If you lose progress, check localStorage for saved data
- Use browser DevTools: `localStorage.getItem('scriptData')`

## Environment Variables (Already Configured)

The following are already set in your project:
- ✅ `ELEVENLABS_API_KEY`
- ✅ `OPENAI_API_KEY` (for DALL-E 3)
- ✅ `RUNWAY_API_KEY` (for video generation)

## Development Mode

To see mock data without using API credits:
```bash
# Set in .env.local
USE_MOCK_AUDIO=true
USE_MOCK_IMAGES=true
USE_MOCK_VIDEOS=true
```

## Production Build

For production deployment:
```bash
# Build the application
npm run build

# Start production server
npm start
```

---

Enjoy creating AI-powered videos with the Evergreen Production Pipeline! 🎬✨