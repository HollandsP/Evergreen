# CLAUDE.md - AI Agent Collaboration Guidelines

## 🤖 ATTENTION: AI Agents Working on This Repository

This document contains critical instructions for AI agents (Claude, GPT, Gemini, etc.) working on the AI Content Generation Pipeline project. **ALL AI AGENTS MUST READ AND FOLLOW THESE GUIDELINES.**

---

## 🚨 MANDATORY: Update Work Log

**EVERY AI AGENT MUST**:
1. Read this file at the start of each session
2. Update `AGENT_WORK_LOG.md` with your contributions
3. Commit and push changes to GitHub before ending session

```bash
# Required commands at session end:
git add AGENT_WORK_LOG.md
git commit -m "Update agent work log - [Your Agent Name] - [Date]"
git push origin main  # or appropriate branch
```

---

## 📋 Project Overview

**Project**: AI Content Generation Pipeline  
**Purpose**: Automated YouTube video generation from narrative scripts  
**Tech Stack**: Python, FastAPI, Celery, Docker, FFmpeg  
**Key Services**: ElevenLabs (voice), Runway Gen-2 (video)

### Critical Files to Know:
- `PRD.md` - Product requirements (READ FIRST)
- `architecture.md` - System design and components
- `IMPLEMENTATION_WORKFLOW.md` - Development phases and tasks
- `README.md` - Setup and usage instructions

---

## 🛠️ Development Guidelines

### 1. Code Standards
```python
# Always follow these patterns:
- Type hints for all functions
- Docstrings for all classes/methods
- Async/await for I/O operations
- Error handling with proper logging
- Unit tests for new functionality
```

### 2. Project Structure
```
src/
├── core/           # Shared utilities (DON'T modify without discussion)
├── script_engine/  # Script parsing and processing
├── voice_synthesis/# Voice generation integration
├── visual_engine/  # Video generation components
├── terminal_sim/   # Terminal UI effects
└── assembly/       # Media assembly pipeline
```

### 3. API Patterns
- All endpoints in `api/routes/`
- Use Pydantic models for validation
- Return consistent error responses
- Document with OpenAPI annotations

### 4. Testing Requirements
- Write tests BEFORE implementation
- Minimum 80% coverage for new code
- Use pytest fixtures for common setups
- Mock external API calls

---

## 📝 Work Log Requirements

When updating `AGENT_WORK_LOG.md`, include:

```markdown
## [Date] - [Your Agent Name] - Session [Number]

### Summary
Brief description of work completed

### Files Modified
- `path/to/file1.py` - Description of changes
- `path/to/file2.md` - Description of changes

### Features Implemented
- Feature 1: Description and status
- Feature 2: Description and status

### Tests Added
- Test file and what it covers

### Issues Encountered
- Any blockers or concerns

### Next Steps
- What needs to be done next
- Recommendations for next agent

### Time Spent
- Estimated time: X hours
```

---

## ⚠️ Critical Warnings

### DO NOT:
- Modify database schema without updating migrations
- Change API contracts without versioning
- Remove existing tests (only add or improve)
- Commit API keys or secrets
- Skip error handling for external services
- Ignore the cost implications of AI API calls

### ALWAYS:
- Run tests before committing: `pytest tests/`
- Check linting: `flake8 src/ api/`
- Update documentation for new features
- Consider API rate limits in implementations
- Add retry logic for external services
- Log all errors with context

---

## 🔑 Environment Setup

### Required Environment Variables:
```bash
ELEVENLABS_API_KEY=<required>
RUNWAY_API_KEY=<optional for MVP>
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
AWS_ACCESS_KEY_ID=<for S3>
AWS_SECRET_ACCESS_KEY=<for S3>
```

### Quick Start Commands:
```bash
# Setup environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run services
docker-compose up -d

# Run tests
pytest tests/

# Start development server
uvicorn api.main:app --reload
```

---

## 🎯 Current Project Status

### Completed:
- ✅ Project structure and scaffolding
- ✅ Documentation (PRD, Architecture, API Spec)
- ✅ Implementation workflow
- ✅ Development environment setup

### In Progress:
- 🔄 Phase 1: Foundation & Infrastructure (Weeks 1-2)
- 🔄 Database schema implementation
- 🔄 Core API setup

### Upcoming:
- ⏳ Script engine implementation
- ⏳ Voice synthesis integration
- ⏳ Terminal UI simulator
- ⏳ Video generation integration

---

## 💬 Communication Patterns

### Git Commit Messages:
```
feat: Add script parsing endpoint
fix: Resolve memory leak in video processing
docs: Update API documentation for v1.1
test: Add integration tests for voice synthesis
refactor: Optimize database queries for performance
```

### PR Description Template:
```markdown
## Summary
What does this PR do?

## Changes
- List of specific changes

## Testing
- How to test these changes

## Related Issues
- Links to related issues/tasks
```

---

## 🚀 Performance Considerations

### Critical Metrics:
- Script processing: <30 seconds
- Voice generation: <2 minutes per character
- Video generation: <10 minutes per scene
- Total pipeline: <2 hours per video
- API response time: <500ms

### Optimization Priority:
1. Database query optimization
2. Caching frequently accessed data
3. Parallel processing where possible
4. Efficient queue management
5. CDN usage for media delivery

---

## 🔐 Security Requirements

### Always Implement:
- Input validation and sanitization
- SQL injection prevention
- Rate limiting on all endpoints
- Secure API key storage (use environment variables)
- HTTPS for all communications
- Audit logging for sensitive operations

### Never Commit:
- API keys or secrets
- Database credentials
- AWS access keys
- Personal information
- Test data with real user info

---

## 📚 Resource Links

### Documentation:
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/best-practices/)
- [Celery Documentation](https://docs.celeryproject.org/)
- [FFmpeg Python](https://github.com/kkroening/ffmpeg-python)
- [ElevenLabs API](https://docs.elevenlabs.io/api-reference/introduction)

### Internal Docs:
- API Specification: `docs/api-specification.md`
- Deployment Guide: `docs/deployment.md`
- Architecture Details: `architecture.md`

---

## 🤝 Collaboration Protocol

### Before Starting Work:
1. Read latest updates in `AGENT_WORK_LOG.md`
2. Check current git branch and status
3. Pull latest changes: `git pull origin main`
4. Review any failing tests or CI/CD issues

### During Work:
1. Create feature branch: `git checkout -b feature/description`
2. Make atomic commits with clear messages
3. Run tests frequently
4. Update documentation as you go

### Before Ending Session:
1. Ensure all tests pass
2. Update `AGENT_WORK_LOG.md`
3. Commit all changes
4. Push to GitHub
5. Note any unfinished work for next agent

---

## 🎨 Code Examples

### Script Parser Pattern:
```python
from typing import List, Dict
from pydantic import BaseModel

class ScriptSegment(BaseModel):
    text: str
    speaker: str
    duration: float
    timestamp: float

class ScriptParser:
    async def parse_markdown(self, content: str) -> List[ScriptSegment]:
        """Parse markdown content into script segments."""
        # Implementation here
        pass
```

### API Endpoint Pattern:
```python
from fastapi import APIRouter, HTTPException
from typing import List

router = APIRouter()

@router.post("/parse", response_model=List[ScriptSegment])
async def parse_script(content: str):
    """Parse script content into segments."""
    try:
        parser = ScriptParser()
        segments = await parser.parse_markdown(content)
        return segments
    except Exception as e:
        logger.error(f"Script parsing failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
```

### Test Pattern:
```python
import pytest
from fastapi.testclient import TestClient

def test_parse_script(client: TestClient):
    """Test script parsing endpoint."""
    response = client.post("/api/v1/scripts/parse", json={
        "content": "# Test Script\n\nSpeaker: Test dialogue"
    })
    assert response.status_code == 200
    assert len(response.json()) > 0
```

---

## ❓ Common Issues & Solutions

### Issue: Docker containers not starting
```bash
# Solution:
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Issue: Database migrations failing
```bash
# Solution:
docker-compose exec db psql -U pipeline -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
python scripts/init_db.py
```

### Issue: API rate limits hit
```python
# Solution: Implement exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def call_external_api():
    # API call here
    pass
```

---

## 📞 Getting Help

### If Stuck:
1. Check existing documentation thoroughly
2. Review similar implementations in codebase
3. Look for patterns in test files
4. Document the issue in work log
5. Leave detailed notes for next agent

### Priority Support Areas:
- Database design decisions
- API contract changes
- Security implementations
- Cost optimization strategies
- Performance bottlenecks

---

**Remember**: Your work directly impacts the project's success. Take time to understand the context, write quality code, and document your contributions thoroughly. The next agent depends on your clear communication!

**Last Updated**: January 2025  
**Version**: 1.0