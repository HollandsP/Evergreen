# OpenAI-Powered Pipeline Design (DALL-E 3 + Future Sora)

## Updated Architecture with OpenAI Services

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Current Pipeline                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  [Text] ──► [DALL-E 3] ──► [Image] ──► [RunwayML] ──► [Video]         │
│                                           gen4_turbo                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                     Future Pipeline (When Sora Available)                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Option 1: [Text] ──► [Sora] ──► [Video] (Direct text-to-video)        │
│                                                                          │
│  Option 2: [Text] ──► [Sora] ──► [Image] ──► [Sora] ──► [Video]       │
│            (Sora for both image and video generation)                    │
│                                                                          │
│  Option 3: [Image Upload] ──► [Sora] ──► [Video]                       │
│            (Sora can animate existing images)                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 1. DALL-E 3 Integration Service

```python
from openai import OpenAI
import aiohttp
from PIL import Image
import io
import base64

class OpenAIImageGenerator:
    """DALL-E 3 integration for image generation"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "dall-e-3"
        
    async def generate_image(
        self,
        prompt: str,
        size: str = "1792x1024",  # Best for 16:9 conversion
        quality: str = "hd",
        style: str = "natural",  # or "vivid"
        n: int = 1
    ) -> Dict[str, Any]:
        """
        Generate image with DALL-E 3
        
        Args:
            prompt: Text description
            size: "1024x1024", "1792x1024", or "1024x1792"
            quality: "standard" ($0.040) or "hd" ($0.080)
            style: "natural" or "vivid"
        """
        
        # Enhance prompt for better RunwayML compatibility
        enhanced_prompt = self._enhance_for_video(prompt)
        
        try:
            response = await self.client.images.generate(
                model=self.model,
                prompt=enhanced_prompt,
                size=size,
                quality=quality,
                style=style,
                n=n,
                response_format="url"  # or "b64_json"
            )
            
            image_url = response.data[0].url
            
            # Resize for RunwayML if needed
            if size != "1792x1024":
                image_url = await self._resize_for_runway(image_url)
            
            return {
                "image_url": image_url,
                "revised_prompt": response.data[0].revised_prompt,
                "cost": 0.080 if quality == "hd" else 0.040
            }
            
        except Exception as e:
            logger.error(f"DALL-E 3 generation failed: {e}")
            raise
    
    def _enhance_for_video(self, prompt: str) -> str:
        """Enhance prompt for better video generation"""
        # Add modifiers that help with video consistency
        video_modifiers = [
            "cinematic composition",
            "consistent lighting",
            "clear focal point",
            "film still",
            "establishing shot"
        ]
        
        # Add random modifier for variety
        modifier = random.choice(video_modifiers)
        
        return f"{prompt}, {modifier}, high quality, detailed"
    
    async def _resize_for_runway(self, image_url: str) -> str:
        """Resize image to 1280x720 for RunwayML"""
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as resp:
                image_data = await resp.read()
        
        # Open and resize
        img = Image.open(io.BytesIO(image_data))
        
        # Smart crop to 16:9
        if img.width / img.height > 16/9:
            # Image is too wide, crop width
            new_width = int(img.height * 16/9)
            left = (img.width - new_width) // 2
            img = img.crop((left, 0, left + new_width, img.height))
        else:
            # Image is too tall, crop height
            new_height = int(img.width * 9/16)
            top = (img.height - new_height) // 2
            img = img.crop((0, top, img.width, top + new_height))
        
        # Resize to exact dimensions
        img = img.resize((1280, 720), Image.Resampling.LANCZOS)
        
        # Convert to base64 data URI
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
```

## 2. Hybrid Pipeline Manager

```python
class HybridPipelineManager:
    """Manage multiple image/video generation backends"""
    
    def __init__(self):
        self.dalle = OpenAIImageGenerator()
        self.flux = FluxImageGenerator()  # Keep as backup
        self.runway = RunwayMLProperClient()
        
        # Future: self.sora = OpenAISoraGenerator()
        
    async def generate_clip(
        self,
        text_prompt: str,
        image_backend: str = "dalle3",  # or "flux"
        video_backend: str = "runway",  # future: "sora"
        **kwargs
    ) -> Dict[str, Any]:
        """Generate clip with selected backends"""
        
        # Step 1: Generate image
        if image_backend == "dalle3":
            image_result = await self.dalle.generate_image(
                prompt=text_prompt,
                quality="hd",
                style=kwargs.get("style", "natural")
            )
            image_url = image_result["image_url"]
            
        elif image_backend == "flux":
            image_result = await self.flux.generate_image(
                prompt=text_prompt,
                style=kwargs.get("style", "photorealistic")
            )
            image_url = image_result["image_url"]
        
        # Step 2: Generate video
        if video_backend == "runway":
            video_prompt = self._create_video_prompt(text_prompt)
            
            task = self.runway.generate_video_from_image(
                image_url=image_url,
                prompt=video_prompt,
                duration=kwargs.get("duration", 10),
                model="gen4_turbo"
            )
            
            video_url = await self.runway.wait_for_completion_async(task["id"])
            
        # Future: elif video_backend == "sora":
        #     video_url = await self.sora.generate_video(...)
        
        return {
            "image_url": image_url,
            "video_url": video_url,
            "backends_used": {
                "image": image_backend,
                "video": video_backend
            },
            "cost_breakdown": {
                "image": 0.08 if image_backend == "dalle3" else 0.10,
                "video": 0.50  # RunwayML cost
            }
        }
```

## 3. Web Interface Updates

```typescript
// Updated component with backend selection
const ImageGeneratorPanel: React.FC = () => {
  const [imageBackend, setImageBackend] = useState<"dalle3" | "flux">("dalle3");
  const [videoBackend, setVideoBackend] = useState<"runway" | "sora">("runway");
  
  return (
    <div className="generator-panel">
      <div className="backend-selector">
        <label>Image Generator:</label>
        <select 
          value={imageBackend} 
          onChange={(e) => setImageBackend(e.target.value as any)}
        >
          <option value="dalle3">DALL-E 3 (OpenAI) - $0.08/image</option>
          <option value="flux">Flux.1 Pro - $0.10/image</option>
        </select>
        
        <label>Video Generator:</label>
        <select 
          value={videoBackend}
          onChange={(e) => setVideoBackend(e.target.value as any)}
        >
          <option value="runway">RunwayML Gen-4 - $0.50/10s</option>
          <option value="sora" disabled>
            Sora (Coming Soon) - TBD
          </option>
        </select>
      </div>
      
      {imageBackend === "dalle3" && (
        <div className="dalle-options">
          <label>Style:</label>
          <select>
            <option value="natural">Natural (Photorealistic)</option>
            <option value="vivid">Vivid (More Artistic)</option>
          </select>
          
          <label>Quality:</label>
          <select>
            <option value="hd">HD - $0.08</option>
            <option value="standard">Standard - $0.04</option>
          </select>
        </div>
      )}
    </div>
  );
};
```

## 4. Cost Comparison

### Current Pipeline Costs (per 10-second clip):
- **DALL-E 3 + RunwayML**: $0.08 + $0.50 = $0.58
- **Flux.1 + RunwayML**: $0.10 + $0.50 = $0.60

### Future with Sora (estimated):
- **DALL-E 3 + Sora**: $0.08 + $0.25? = $0.33?
- **Direct Sora**: $0.30? = $0.30?

## 5. Advantages of OpenAI Stack

### Immediate Benefits:
1. **Single API Key**: Use existing OpenAI key for images
2. **Better Prompt Understanding**: DALL-E 3 excels at complex prompts
3. **Consistent Style**: Easier to maintain visual consistency
4. **Built-in Safety**: Less moderation issues
5. **Cost Effective**: Slightly cheaper than Flux.1

### Future Benefits (with Sora):
1. **Full OpenAI Pipeline**: Image + Video from same provider
2. **Better Integration**: Designed to work together
3. **Longer Videos**: Sora supports up to 60 seconds
4. **Higher Quality**: Sora demos show superior quality
5. **Direct Text-to-Video**: Skip image step entirely

## 6. Implementation Priority

### Phase 1: DALL-E 3 Integration (Immediate)
```python
# Quick implementation example
async def test_dalle3_to_runway():
    """Test DALL-E 3 → RunwayML pipeline"""
    
    # Generate image with DALL-E 3
    openai_gen = OpenAIImageGenerator()
    image_result = await openai_gen.generate_image(
        prompt="A serene mountain lake at sunrise, cinematic composition",
        size="1792x1024",
        quality="hd",
        style="natural"
    )
    
    print(f"DALL-E 3 Image: {image_result['image_url']}")
    print(f"Revised prompt: {image_result['revised_prompt']}")
    
    # Generate video with RunwayML
    runway = RunwayMLProperClient()
    task = runway.generate_video_from_image(
        image_url=image_result['image_url'],
        prompt="Camera slowly pulls back revealing the full mountain landscape",
        duration=10,
        model="gen4_turbo"
    )
    
    video_url = await runway.wait_for_completion_async(task['id'])
    print(f"RunwayML Video: {video_url}")
    
    return {
        "total_cost": 0.58,
        "image_url": image_result['image_url'],
        "video_url": video_url
    }
```

### Phase 2: Prepare for Sora (Future)
- Design API abstraction layer
- Create fallback mechanisms
- Build queue system for when available
- Prepare UI for backend switching

## 7. Recommended Approach

### Use DALL-E 3 as Primary because:
1. ✅ Already have API access
2. ✅ Cheaper than Flux.1
3. ✅ Better prompt adherence
4. ✅ Smoother future transition to Sora
5. ✅ Single vendor simplicity

### Keep Flux.1 as Backup for:
1. When specific artistic styles needed
2. If OpenAI has downtime
3. User preference option
4. A/B testing quality

### Prepare for Sora by:
1. Building flexible backend system
2. Creating video-first prompting
3. Designing 60-second clip workflows
4. Planning cost optimization strategies