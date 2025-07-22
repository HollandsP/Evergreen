# ✅ Production Pipeline Testing Checklist

Quick checklist to verify all features are working correctly with your API keys.

## Pre-Flight Checks

- [ ] Server running: `npm run dev`
- [ ] Navigate to: http://localhost:3000/production
- [ ] WebSocket shows "Connected" (green indicator in header)

## Stage 1: Script Processing ✍️

- [ ] Upload test script: `/scripts/ScriptLog0002TheDescent.txt`
- [ ] Verify 8 scenes are parsed correctly
- [ ] Check timestamps show properly (0:00, 0:20, etc.)
- [ ] Narration text is extracted for Winston
- [ ] On-screen text displays in terminal style
- [ ] Image prompts are auto-generated
- [ ] Can edit narration text inline
- [ ] "Continue" button becomes active

## Stage 2: Audio Generation 🎙️

- [ ] Previous script data loads correctly
- [ ] Voice selection shows Winston options
- [ ] "Generate All Audio" button works
- [ ] Progress bar shows generation status
- [ ] Audio files play in browser
- [ ] Waveform visualization appears
- [ ] Duration is displayed for each clip
- [ ] Can download individual audio files

## Stage 3: Image Generation 🎨

- [ ] Script and audio data persist
- [ ] DALL-E 3 is the only provider shown
- [ ] Cost estimate shows ~$0.32 for 8 images
- [ ] Prompts are pre-filled and editable
- [ ] "Generate All Images" starts batch process
- [ ] Progress updates in real-time
- [ ] Images display in gallery view
- [ ] Can upload custom images as alternative
- [ ] Each image shows "Completed" status

## Stage 4: Video Generation 🎬

- [ ] All previous data loads correctly
- [ ] Timeline shows audio waveform
- [ ] Video prompts are editable
- [ ] Camera movements dropdown works
- [ ] Motion intensity slider is responsive
- [ ] Lip-sync auto-enabled for dialogue
- [ ] "Generate All Videos" processes batch
- [ ] Videos play with synchronized audio
- [ ] Duration matches audio length

## Stage 5: Final Assembly 🎞️

- [ ] Timeline shows all video clips
- [ ] Can drag to reorder scenes
- [ ] Transition effects are selectable
- [ ] Background music upload works
- [ ] Volume sliders adjust properly
- [ ] Export settings show options
- [ ] "Export Video" starts processing
- [ ] Progress bar shows assembly status
- [ ] Final video downloads successfully

## API Integration Tests

### ElevenLabs (Audio)
- [ ] Generates real MP3 files
- [ ] Voice matches selection
- [ ] No 401/403 errors

### DALL-E 3 (Images)
- [ ] Generates 1792x1024 images
- [ ] Images match prompts
- [ ] No content policy violations

### RunwayML (Video)
- [ ] Creates video files
- [ ] Videos have motion
- [ ] Duration matches request

## Error Handling

- [ ] Invalid file type shows error
- [ ] Empty script shows warning
- [ ] API failures show user-friendly messages
- [ ] Can retry failed operations
- [ ] Progress doesn't get stuck

## Performance

- [ ] Page loads quickly
- [ ] No memory leaks during long sessions
- [ ] Batch operations complete efficiently
- [ ] UI remains responsive during generation

## State Persistence

- [ ] Refresh page at Stage 3 - data persists
- [ ] Browser back/forward maintains state
- [ ] Can resume from any stage
- [ ] Production state updates correctly

## Quick Test Commands

```bash
# Check if all dependencies are installed
npm list

# Run type checking
npm run type-check

# Run tests
npm test

# Check for linting issues
npm run lint
```

## If Something Fails

1. Check browser console for errors
2. Verify API keys in `.env.local`
3. Check network tab for failed requests
4. Look at terminal for server errors
5. Try with mock data: `USE_MOCK_AUDIO=true`

---

**Expected Full Pipeline Time**: ~5-10 minutes for complete video generation