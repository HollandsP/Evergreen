# Image-to-Video Workflow Implementation Plan

## Executive Summary

Based on comprehensive analysis of the Evergreen codebase, the core infrastructure for image-to-video generation already exists. The critical issue is that users cannot access or use this functionality due to UI/UX problems. This plan addresses these issues with minimal code changes for maximum impact.

## Current State Analysis

### What's Working ✅
1. **Image Generation Component** (`ImageGenerator.tsx`)
   - DALL-E 3 integration functional
   - Images stored in localStorage with URLs and prompts
   - Each scene properly tracked with status

2. **Video Generation API** (`/api/videos/generate.ts`)
   - Accepts `imageUrl` parameter
   - Designed for Runway Gen-4 Turbo integration
   - Camera movement and motion intensity controls

3. **Data Flow**
   - Images are loaded in VideoGenerator component
   - Image URLs are attached to scenes
   - Video generation API receives image URLs

### What's Broken ❌
1. **Navigation Completely Disabled**
   - All stages except "script" marked as `disabled` and `isAvailable: false`
   - Users cannot click on Image or Video generation stages
   - Auto-redirect forces users to script stage only

2. **Prompt Workflow Disconnected**
   - Image prompts stored separately from video prompts
   - No inheritance or transformation between stages
   - Users must manually rewrite prompts for video

3. **Missing Visual Feedback**
   - No large image preview in video stage
   - No indication of prompt relationship
   - No edit capability for prompts during video generation

## Implementation Plan

### Phase 1: Enable Navigation (30 minutes)
**Priority: CRITICAL - Without this, nothing else matters**

1. **Fix Stage Navigation** (`StageNavigation.tsx`)
   ```typescript
   // Change all stages to be available after script is completed
   isAvailable: true  // for all stages
   status: 'pending' // instead of 'disabled'
   ```

2. **Remove Auto-Redirect** (`/production/index.tsx`)
   ```typescript
   // Comment out or remove:
   // router.push('/production/script');
   ```

3. **Add Stage Progression Logic**
   - Script completion enables Audio
   - Audio completion enables Images
   - Images completion enables Videos
   - Videos completion enables Assembly

### Phase 2: Prompt Inheritance System (1 hour)
**Priority: HIGH - Core user requirement**

1. **Create Prompt Transformer** (`/lib/prompt-transformer.ts`)
   ```typescript
   export function transformImageToVideoPrompt(
     imagePrompt: string,
     sceneType: string,
     duration: number
   ): string {
     // Add motion descriptors
     // Add camera movement suggestions
     // Maintain visual consistency keywords
   }
   ```

2. **Update Video Generator Component**
   - Auto-populate video prompts from image prompts
   - Show both prompts side-by-side
   - Allow editing while preserving original

3. **Prompt Templates by Scene Type**
   - Action scenes: Add "dynamic movement, fast cuts"
   - Dialogue scenes: Add "subtle movement, focus on speaker"
   - Establishing shots: Add "slow pan, atmospheric"

### Phase 3: Enhanced Image Preview (45 minutes)
**Priority: HIGH - User visibility requirement**

1. **Add Image Gallery to Video Stage**
   ```typescript
   // Large preview images
   // Click to view full-size
   // Show image prompt below each image
   ```

2. **Visual Prompt Editor**
   - Side-by-side image and prompt
   - Real-time preview of prompt changes
   - Suggested motion keywords

3. **Image-to-Video Relationship**
   - Visual connection lines
   - Progress indicators
   - Success/error states

### Phase 4: Real RunwayML Integration (2 hours)
**Priority: MEDIUM - Currently using mock API**

1. **Update API Endpoint** (`/api/videos/generate.ts`)
   - Implement actual Runway API calls
   - Add proper error handling
   - Progress webhook integration

2. **Add API Key Management**
   - Environment variable for RUNWAY_API_KEY
   - User settings for API configuration
   - Usage tracking and limits

3. **Advanced Options**
   - Motion intensity slider
   - Camera movement selector
   - Lip-sync toggle for dialogue

### Phase 5: Workflow Enhancements (1 hour)
**Priority: LOW - Nice to have**

1. **Batch Operations**
   - Generate all videos at once
   - Parallel processing
   - Queue management

2. **Preview System**
   - Thumbnail generation
   - Quick preview before full generation
   - A/B testing different prompts

3. **Save/Load Workflows**
   - Save prompt templates
   - Share workflows between projects
   - Version control for prompts

## Implementation Order

1. **MUST DO FIRST**: Enable navigation (Phase 1)
   - Without this, users can't even see the image generation stage
   - This is the root cause of user frustration

2. **CORE FEATURE**: Prompt inheritance (Phase 2)
   - This is what the user specifically requested
   - "generate a video from an image (with prompt also)"

3. **USER EXPERIENCE**: Enhanced preview (Phase 3)
   - Makes the workflow visible and understandable
   - Reduces user confusion

4. **PRODUCTION READY**: Real API integration (Phase 4)
   - Currently returns mock videos
   - Needed for actual video generation

5. **NICE TO HAVE**: Workflow enhancements (Phase 5)
   - Improves efficiency for power users
   - Not critical for MVP

## Success Metrics

1. **Navigation Working**: User can click through all 5 stages
2. **Prompts Connected**: Image prompts auto-populate video prompts
3. **Visual Feedback**: User can see images while generating videos
4. **Real Videos**: Actual video files generated (not mock URLs)
5. **Complete Workflow**: Script → Audio → Images → Videos → Assembly

## Risk Mitigation

1. **Backwards Compatibility**: Keep existing localStorage structure
2. **Graceful Degradation**: Mock API fallback if Runway unavailable
3. **Data Preservation**: Never lose user's work during transitions
4. **Clear Errors**: Helpful messages if something fails

## Estimated Timeline

- **Phase 1**: 30 minutes (Critical fix)
- **Phase 2**: 1 hour (Core feature)
- **Phase 3**: 45 minutes (UX improvement)
- **Phase 4**: 2 hours (API integration)
- **Phase 5**: 1 hour (Enhancements)

**Total**: ~5.25 hours for complete implementation

## Quick Win

The fastest way to satisfy the user's immediate need:
1. Enable navigation (5 minutes)
2. Add prompt copying from image to video (15 minutes)
3. Show images in video generator (10 minutes)

**30 minutes to basic functionality**

## Conclusion

The user's frustration is completely justified. The infrastructure exists but is hidden behind disabled navigation and poor UX. The fix is straightforward - enable the stages and connect the prompts. This plan provides a clear path from the current broken state to a fully functional image-to-video workflow.