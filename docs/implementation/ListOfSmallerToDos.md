# List of Smaller ToDos - Deferred Items

This document tracks smaller implementation items that were identified but deferred to maintain development velocity. These items are functional but could be enhanced.

## Cycle 1 - Deferred Items (10% Remaining)

### 1. S3 Storage Integration
- **Current State**: Audio files generate locally in `/tmp/` directory
- **Needed**: Upload generated audio files to S3 after creation
- **Location**: `web/pages/api/audio/generate.ts` - See TODO comment
- **Priority**: Medium - Local storage works for development

### 2. Quality Assessment Metrics
- **Current State**: Returns random values between 75-95%
- **Needed**: Implement real quality scoring based on generation parameters
- **Locations**: 
  - `web/pages/api/projects/[id]/quality.ts`
  - `web/pages/api/quality/assess.ts`
- **Priority**: Low - Placeholder values sufficient for MVP

### 3. Backend Service Dependency
- **Current State**: Frontend expects FastAPI backend at localhost:8000
- **Needed**: Add health check and graceful fallback when backend unavailable
- **Location**: API proxy configuration in `next.config.js`
- **Priority**: Medium - Works when both services running

### 4. Development Mock Endpoints
- **Current State**: `/api/audio/mock/[sceneId].ts` exists for development
- **Needed**: Clean up or clearly mark as development-only
- **Priority**: Low - Useful for testing without API costs

### 5. Environment Variable Validation
- **Current State**: API keys checked at request time
- **Needed**: Startup validation with clear error messages
- **Priority**: Low - Current runtime checks are sufficient

## Cycle 2 - Deferred Items (Backend Integration Issues)

### 1. RunwayML API Integration Testing ⚠️
- **Current State**: Client code exists but no evidence of real video generation
- **Issue**: Found placeholder mock implementations in AssetLibrary.tsx
- **Needed**: Test actual RunwayML Gen-3 Alpha Turbo video generation
- **Priority**: HIGH - Core feature missing

### 2. WebSocket Server Implementation
- **Current State**: Frontend WebSocket manager ready but no server
- **Issue**: Real-time progress updates not functional
- **Needed**: Implement WebSocket server in FastAPI or Next.js
- **Priority**: Medium - Affects user experience

### 3. Server-Side Folder Management
- **Current State**: Frontend folder logic only
- **Issue**: No persistent file system organization
- **Needed**: Implement `/api/projects/[projectId]/folders.ts` endpoint
- **Priority**: Medium - File organization not persistent

### 4. AI Video Editor Backend
- **Current State**: Chat interface exists but no backend integration
- **Issue**: No actual video editing capabilities
- **Needed**: Connect GPT-4 command parsing to MoviePy/FFmpeg
- **Priority**: Medium - Advanced feature for Cycle 3

### 5. PDF Upload Support
- **Current State**: Mentioned in UI but not implemented
- **Issue**: Only .txt and .md files actually supported
- **Needed**: Add PDF parsing capability
- **Priority**: Low - Nice to have feature

### 6. SECURITY ISSUE: Real API Keys in Repository 🚨
- **Current State**: `.env.example` contains REAL API keys
- **Issue**: Security vulnerability - keys exposed in version control
- **Needed**: Replace with placeholder values immediately
- **Priority**: CRITICAL - Security risk

## Cycle 3 - Deferred Items
_To be populated after Cycle 3 completion_

---

**Note**: These items represent enhancements rather than critical functionality. The core features work without them.