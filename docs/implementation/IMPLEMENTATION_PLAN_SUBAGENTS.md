# 🚀 EVERGREEN AI VIDEO PIPELINE - PARALLEL IMPLEMENTATION PLAN

## 📋 Overview
This plan breaks down the implementation into parallel sub-agent tasks that can be executed simultaneously to rapidly fix the Evergreen AI Video Pipeline. Each sub-agent has a specific focus area and clear deliverables.

**CORE DIRECTIVE**: NO NEW FEATURES! Only fix existing functionality and remove bloat.

---

## 🔴 CYCLE 1: CORE PIPELINE FIX (Remove Bloat & Connect Services)

### Sub-Agent 1: Bloat Remover
**Persona**: `--persona-refactorer`
**Priority**: CRITICAL
**Estimated Time**: 1-2 hours

**PROMPT**:
```
You are working on the Evergreen AI Video Pipeline project. Your task is to remove all unnecessary bloat added by Agent 4D-4H. 

MANDATORY DELETIONS:
1. Frontend Components (web/components/editor/):
   - Timeline.tsx, CollaborativeEditor.tsx, SmartSuggestions.tsx, BulkOperations.tsx
   - ExportPresets.tsx, OperationQueue.tsx, OperationTemplates.tsx, PreviewScrubber.tsx
   - QuickTemplates.tsx, VideoPreview.tsx

2. Backend Services (src/services/):
   - advanced_transitions.py, ai_color_enhancer.py, ai_scene_analyzer.py, ai_scene_detector.py
   - audio_sync_processor.py, color_grading_engine.py, intelligent_cropping.py
   - scene_reordering_engine.py, smart_audio_balancer.py, subtitle_generator.py
   - text_animation_engine.py, video_stabilizer.py, corruption_detector.py, graceful_degradation.py

3. Test Folders:
   - Delete entire folders: tests/performance/, tests/stress/, tests/visual/
   - Delete files: tests/integration/test_professional_*.py, tests/run_agent_4c_tests.py

4. Root Directory Cleanup:
   - Delete all .txt files EXCEPT requirements.txt and requirements-dev.txt
   - Delete: CYCLE_4_AGENT_PROMPTS.md, AGENT_4I_AI_INTEGRATION_PLAN.md
   - Delete: SCENE_PERFORMANCE_OPTIMIZATION.md, VIDEO_OPTIMIZATION_README.md

After deletion:
- Update any imports that reference deleted files
- Ensure the application still compiles
- Commit with message: "Remove Agent 4D-4H bloat - cleaned 50+ unnecessary files"
```

### Sub-Agent 2: Backend Connector
**Persona**: `--persona-backend`
**Priority**: CRITICAL
**Estimated Time**: 2-3 hours

**PROMPT**:
```
You are working on the Evergreen AI Video Pipeline project. Your task is to connect the Next.js frontend to the Python FastAPI backend.

REQUIRED TASKS:
1. Environment Setup:
   - Add to .env: PYTHON_API_URL=http://localhost:8000
   - Add to .env: BACKEND_WS_URL=ws://localhost:8000/ws
   - Ensure .env.example is updated

2. Fix API Connection (web/pages/api/editor/process-command.ts):
   - Properly read PYTHON_API_URL from environment
   - Add error handling for backend connection
   - Test connection to api/routes/editor.py

3. WebSocket Backend Connection:
   - Update web/pages/api/socket.ts to connect to Python WebSocket
   - Remove simulateJobUpdates mock function
   - Implement real backend WebSocket relay

4. Python Backend Updates:
   - Create api/websocket.py for WebSocket server
   - Update api/main.py to include WebSocket endpoint
   - Ensure CORS is properly configured for frontend access

5. Test the connection:
   - Verify frontend can call Python endpoints
   - Verify WebSocket events flow from backend to frontend
   - Document the startup process in README

Commit with message: "Connect frontend to Python backend - fix API and WebSocket integration"
```

### Sub-Agent 3: File Organization Manager
**Persona**: `--persona-architect`
**Priority**: HIGH
**Estimated Time**: 2-3 hours

**PROMPT**:
```
You are working on the Evergreen AI Video Pipeline project. Your task is to implement proper file organization and scene metadata management.

REQUIRED TASKS:
1. Create Centralized File Manager (web/lib/file-manager.ts):
   ```typescript
   class ProjectFileManager {
     - Define consistent folder structure: projects/{projectId}/scenes/{sceneId}/{audio|images|videos}
     - Implement methods: getScenePath, getAssetPath, createProjectStructure
     - Handle file organization for all pipeline stages
   }
   ```

2. Update All File References:
   - web/pages/api/script/parse.ts - Save parsed scenes to project folder
   - web/pages/api/audio/generate.ts - Save audio to scene folders
   - web/pages/api/images/generate.ts - Save images to scene folders
   - web/pages/api/videos/generate.ts - Save videos to scene folders

3. Implement Scene Metadata:
   - Create metadata.json for each project
   - Store scene information, file paths, generation parameters
   - Update metadata as pipeline progresses

4. Fix File Path Issues:
   - Remove all hardcoded paths
   - Use centralized file manager everywhere
   - Ensure paths work on both Windows and Linux

5. Create Project State Manager:
   - Implement persistence of project state
   - Save/load project progress
   - Handle interrupted workflows

Commit with message: "Implement centralized file organization and scene metadata management"
```

### Sub-Agent 4: Pipeline Flow Fixer
**Persona**: `--persona-frontend`
**Priority**: HIGH
**Estimated Time**: 2-3 hours

**PROMPT**:
```
You are working on the Evergreen AI Video Pipeline project. Your task is to fix the production pipeline flow and navigation.

REQUIRED TASKS:
1. Fix Production Page Navigation:
   - Ensure pages flow: script → audio → images → videos → assembly
   - Fix state persistence between pages (use localStorage + API)
   - Update StageNavigation.tsx to properly track completion

2. Connect Pipeline Stages:
   - Pass project ID and scene data between stages
   - Ensure each stage can access previous stage outputs
   - Fix the "Continue" button logic on each page

3. Update Production Pages:
   - /production/script.tsx - Save project ID after parsing
   - /production/audio.tsx - Load scenes, save audio paths
   - /production/images.tsx - Load scenes, save image paths
   - /production/videos.tsx - Load images, save video paths
   - /production/assembly.tsx - Load all media for editing

4. Fix WebSocket Integration:
   - Ensure progress updates work on all pages
   - Show real-time status for long operations
   - Handle errors gracefully with user feedback

5. Add Basic Navigation:
   - Implement "Back" functionality
   - Add "Save & Exit" option
   - Show clear progress indicators

Commit with message: "Fix production pipeline flow and stage navigation"
```

---

## 🟡 CYCLE 2: AI VIDEO EDITOR & EXPORT

### Sub-Agent 5: AI Editor Integration
**Persona**: `--persona-backend`
**Priority**: HIGH
**Estimated Time**: 3-4 hours

**PROMPT**:
```
You are working on the Evergreen AI Video Pipeline project. Your task is to connect the AI video editor chat interface to the Python backend.

REQUIRED TASKS:
1. Connect Chat Interface to Backend:
   - Update web/components/shared/ChatInterface.tsx to call API
   - Fix web/pages/api/editor/process-command.ts to reach Python backend
   - Ensure src/services/ai_video_editor.py processes commands

2. Implement Core Editing Commands:
   - Cut/trim scenes
   - Add fade in/out transitions
   - Combine multiple scenes
   - Adjust audio levels
   - NO ADVANCED FEATURES!

3. File Path Coordination:
   - AI editor must access files from centralized file manager
   - Save edited videos to export folder
   - Update project metadata with edits

4. Real-time Preview:
   - Show editing progress via WebSocket
   - Display preview of edits (use existing preview component)
   - Handle long operations gracefully

5. Error Handling:
   - Clear error messages for users
   - Graceful fallbacks for failed operations
   - Log errors for debugging

Test with: "Combine all scenes with fade transitions between them"

Commit with message: "Connect AI video editor to Python backend"
```

### Sub-Agent 6: Export Implementation
**Persona**: `--persona-frontend`
**Priority**: MEDIUM
**Estimated Time**: 2-3 hours

**PROMPT**:
```
You are working on the Evergreen AI Video Pipeline project. Your task is to implement video export and download functionality.

REQUIRED TASKS:
1. Implement Export Endpoint (web/pages/api/assembly/export.ts):
   - Call Python backend to assemble final video
   - Combine all scene videos with transitions
   - Add audio track to final video
   - Return path to exported video

2. Add Download Functionality:
   - Create download button in assembly page
   - Implement secure file serving
   - Support MP4 format export
   - Show export progress

3. Basic Metadata for YouTube:
   - Add form for title and description
   - Save metadata with exported video
   - Create simple export preset (1080p, good quality)

4. Local Save Option:
   - Allow users to save to custom location
   - Remember last save location
   - Show file size before download

5. YouTube Upload (OPTIONAL - if time permits):
   - Basic OAuth flow
   - Upload video with title/description
   - NO complex features

Commit with message: "Implement video export and download functionality"
```

---

## 🟢 CYCLE 3: POLISH & RELIABILITY

### Sub-Agent 7: Error Handler
**Persona**: `--persona-qa`
**Priority**: MEDIUM
**Estimated Time**: 2-3 hours

**PROMPT**:
```
You are working on the Evergreen AI Video Pipeline project. Your task is to add robust error handling throughout the pipeline.

REQUIRED TASKS:
1. API Error Handling:
   - Add try-catch blocks to all API endpoints
   - Return consistent error format
   - Log errors with context

2. External API Failures:
   - Add retry logic for DALL-E, ElevenLabs, RunwayML
   - Handle rate limits gracefully
   - Show clear error messages to users

3. File Operation Errors:
   - Handle missing files gracefully
   - Check disk space before operations
   - Validate file formats

4. Progress Persistence:
   - Save progress to localStorage frequently
   - Allow resuming interrupted workflows
   - Clear old/corrupted data

5. User Feedback:
   - Show clear error messages (not technical)
   - Provide suggested actions
   - Add "Report Issue" functionality

Commit with message: "Add comprehensive error handling and retry logic"
```

### Sub-Agent 8: UI Polish & Documentation
**Persona**: `--persona-frontend`
**Priority**: LOW
**Estimated Time**: 2-3 hours

**PROMPT**:
```
You are working on the Evergreen AI Video Pipeline project. Your task is to polish the UI and update documentation.

REQUIRED TASKS:
1. UI Cleanup:
   - Remove references to deleted components
   - Ensure dark mode works consistently
   - Fix any broken styles/layouts
   - Make navigation intuitive

2. Update Production UI:
   - Add loading states for all operations
   - Show estimated time remaining
   - Add tooltips for complex features
   - Ensure mobile responsiveness

3. Update README.md:
   - Document ONLY working features
   - Add clear setup instructions
   - Include troubleshooting section
   - Add example workflow

4. Clean Component Structure:
   - Remove unused imports
   - Delete commented code
   - Organize components logically
   - Add basic TypeScript types

5. Final Testing Checklist:
   - Test complete workflow: script → export
   - Verify all API integrations work
   - Check error scenarios
   - Document known limitations

Commit with message: "Polish UI and update documentation for production use"
```

---

## 📊 EXECUTION STRATEGY

### Parallel Execution Groups:

**Group 1 (Start Immediately):**
- Sub-Agent 1: Bloat Remover
- Sub-Agent 2: Backend Connector
- Sub-Agent 3: File Organization Manager
- Sub-Agent 4: Pipeline Flow Fixer

**Group 2 (After Group 1):**
- Sub-Agent 5: AI Editor Integration
- Sub-Agent 6: Export Implementation

**Group 3 (After Group 2):**
- Sub-Agent 7: Error Handler
- Sub-Agent 8: UI Polish & Documentation

### Success Metrics:
1. All bloat removed (50+ files deleted)
2. Frontend connects to Python backend
3. Complete workflow works: upload script → generate content → edit → export
4. No new features added
5. Clean, organized codebase
6. Updated documentation

### Coordination Notes:
- Sub-agents should NOT add new features
- Focus on making existing code work
- Communicate file changes via git commits
- Test integration points between components
- Update AGENT_WORK_LOG.md after each cycle

---

## 🚦 FINAL CHECKLIST

Before marking complete, ensure:
- [ ] Script upload and parsing works
- [ ] Scene folders are created properly
- [ ] Images generate and save to folders
- [ ] Audio generates and saves to folders
- [ ] Videos generate using RunwayML
- [ ] AI editor can process basic commands
- [ ] Export creates downloadable MP4
- [ ] All bloat files removed
- [ ] Documentation reflects reality
- [ ] Complete workflow tested end-to-end