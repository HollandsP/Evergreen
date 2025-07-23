# System Architecture Document
# Evergreen - AI-Powered YouTube Video Studio

## Document Information
- **Version**: 1.0
- **Date**: July 22, 2025
- **Status**: Final Design
- **Audience**: Development Team, DevOps, System Architects

---

## 1. Executive Summary

This document outlines the technical architecture of Evergreen, an AI-powered video production platform. The system follows a microservices architecture with a React/Next.js frontend, Node.js/Python backend services, and integrations with multiple AI providers. The architecture prioritizes scalability, reliability, and maintainability while supporting real-time collaboration and media processing.

### Key Architectural Decisions
- **Microservices**: Separate services for different domains
- **Event-Driven**: Asynchronous processing for media generation
- **API Gateway**: Centralized routing and authentication
- **Containerized**: Docker/Kubernetes for deployment
- **Cloud-Native**: AWS services for infrastructure

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │   Web App       │  │   Mobile App    │  │   API Clients  │  │
│  │  (Next.js)      │  │   (Future)      │  │  (Developers)  │  │
│  └────────┬────────┘  └────────┬────────┘  └───────┬────────┘  │
└───────────┼────────────────────┼────────────────────┼───────────┘
            │                    │                    │
            ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                       API Gateway Layer                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │             Kong/AWS API Gateway                         │   │
│  │    - Authentication  - Rate Limiting  - Routing         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Microservices Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐        │
│  │   Project    │  │    Script    │  │     Media     │        │
│  │   Service    │  │   Service    │  │   Service     │        │
│  └──────────────┘  └──────────────┘  └───────────────┘        │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐        │
│  │     AI       │  │    Video     │  │    Export     │        │
│  │  Orchestrator│  │   Editor     │  │   Service     │        │
│  └──────────────┘  └──────────────┘  └───────────────┘        │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐        │
│  │  PostgreSQL  │  │    Redis     │  │      S3       │        │
│  │   (Primary)  │  │   (Cache)    │  │   (Media)     │        │
│  └──────────────┘  └──────────────┘  └───────────────┘        │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   External Services                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  OpenAI  │  │RunwayML  │  │ElevenLabs│  │ YouTube  │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Component Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| Frontend | Next.js 14, TypeScript | User interface, real-time updates |
| API Gateway | Kong/AWS API Gateway | Routing, auth, rate limiting |
| Project Service | Node.js, Express | Project management, metadata |
| Script Service | Python, FastAPI | Script parsing, scene analysis |
| Media Service | Node.js, Express | Asset management, storage |
| AI Orchestrator | Python, Celery | AI service coordination |
| Video Editor | Python, MoviePy | Video editing operations |
| Export Service | Node.js, FFmpeg | Final rendering, uploads |
| Database | PostgreSQL 14 | Persistent data storage |
| Cache | Redis 7 | Session, queue, cache |
| Object Storage | AWS S3 | Media file storage |

---

## 3. Frontend Architecture

### 3.1 Technology Stack
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript 5.0
- **Styling**: Tailwind CSS with shadcn/ui
- **State Management**: Zustand + React Query
- **Real-time**: Socket.io client
- **Testing**: Jest + React Testing Library

### 3.2 Component Structure

```
web/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Authentication routes
│   ├── (dashboard)/       # Main application
│   │   ├── projects/      # Project management
│   │   └── studio/        # Production studio
│   └── api/               # API routes (BFF)
├── components/
│   ├── storyboard/        # Storyboard components
│   │   ├── Canvas.tsx     # Drawing canvas
│   │   ├── Frame.tsx      # Individual frame
│   │   └── Timeline.tsx   # Frame timeline
│   ├── editor/            # Video editor
│   │   ├── Timeline.tsx   # Video timeline
│   │   ├── Preview.tsx    # Real-time preview
│   │   └── ChatPanel.tsx  # AI chat interface
│   └── ui/                # shadcn/ui components
├── lib/
│   ├── api/               # API client
│   ├── stores/            # Zustand stores
│   └── utils/             # Utilities
└── styles/                # Global styles
```

### 3.3 State Management

```typescript
// Global State Architecture
interface AppState {
  // User & Auth
  user: User | null;
  session: Session | null;
  
  // Project State
  currentProject: Project | null;
  projects: Project[];
  
  // Production State
  storyboard: StoryboardState;
  scenes: Scene[];
  assets: AssetMap;
  
  // UI State
  activeStage: ProductionStage;
  isGenerating: boolean;
  notifications: Notification[];
}

// Real-time Updates
interface WebSocketEvents {
  'generation:progress': (data: ProgressUpdate) => void;
  'asset:created': (data: Asset) => void;
  'project:updated': (data: Project) => void;
  'error:occurred': (data: ErrorEvent) => void;
}
```

### 3.4 Performance Optimizations
- **Code Splitting**: Dynamic imports for heavy components
- **Image Optimization**: Next.js Image with CDN
- **Lazy Loading**: Intersection Observer for media
- **Virtualization**: React Window for long lists
- **Service Worker**: Offline support and caching

---

## 4. Backend Architecture

### 4.1 Service Architecture

#### Project Service (Node.js)
```
Responsibilities:
- Project CRUD operations
- User permissions
- Collaboration features
- Project templates

API Endpoints:
POST   /api/projects
GET    /api/projects/:id
PUT    /api/projects/:id
DELETE /api/projects/:id
GET    /api/projects/:id/collaborators
POST   /api/projects/:id/share
```

#### Script Service (Python)
```
Responsibilities:
- Script parsing and analysis
- Scene division logic
- Character extraction
- Prompt generation

API Endpoints:
POST   /api/scripts/parse
POST   /api/scripts/analyze
GET    /api/scripts/:id/scenes
POST   /api/scripts/:id/divide
GET    /api/scripts/:id/prompts
```

#### Media Service (Node.js)
```
Responsibilities:
- Asset upload/download
- Media processing
- CDN integration
- Storage management

API Endpoints:
POST   /api/media/upload
GET    /api/media/:id
DELETE /api/media/:id
POST   /api/media/process
GET    /api/media/:id/variants
```

#### AI Orchestrator Service (Python)
```
Responsibilities:
- AI service coordination
- Job queue management
- Cost optimization
- Fallback handling

Internal APIs:
- OpenAI integration
- RunwayML integration
- ElevenLabs integration
- Prompt optimization
```

#### Video Editor Service (Python)
```
Responsibilities:
- Timeline management
- Effect application
- Transition handling
- Preview generation

API Endpoints:
POST   /api/editor/timeline
POST   /api/editor/preview
POST   /api/editor/effects
POST   /api/editor/render
POST   /api/editor/chat
```

### 4.2 Database Schema

```sql
-- Core Tables
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    avatar_url TEXT,
    subscription_tier VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE scenes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    scene_number INTEGER NOT NULL,
    title VARCHAR(255),
    description TEXT,
    duration_seconds FLOAT,
    script_content TEXT,
    prompts JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE storyboard_frames (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scene_id UUID REFERENCES scenes(id),
    frame_number INTEGER NOT NULL,
    frame_type VARCHAR(50), -- 'sketch', 'uploaded', 'ai_generated'
    frame_data TEXT, -- Base64 or URL
    shot_type VARCHAR(50),
    camera_angle VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE assets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    scene_id UUID REFERENCES scenes(id),
    asset_type VARCHAR(50), -- 'image', 'audio', 'video'
    source_type VARCHAR(50), -- 'uploaded', 'generated'
    url TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id),
    job_type VARCHAR(50),
    status VARCHAR(50) DEFAULT 'pending',
    progress INTEGER DEFAULT 0,
    input_data JSONB,
    output_data JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_projects_user_id ON projects(user_id);
CREATE INDEX idx_scenes_project_id ON scenes(project_id);
CREATE INDEX idx_assets_project_scene ON assets(project_id, scene_id);
CREATE INDEX idx_jobs_project_status ON generation_jobs(project_id, status);
```

### 4.3 Caching Strategy

```yaml
Cache Layers:
  1. CDN (CloudFront):
     - Static assets (images, videos)
     - API responses (GET requests)
     - TTL: 1 hour to 1 year

  2. Redis Cache:
     - Session data: 24 hours
     - API responses: 5 minutes
     - Generation results: 1 hour
     - User preferences: 7 days

  3. Application Cache:
     - Prompt templates: In-memory
     - AI model configs: In-memory
     - Frequently used data: LRU cache

Cache Invalidation:
  - Tag-based invalidation
  - Event-driven updates
  - TTL expiration
  - Manual purge options
```

---

## 5. AI Integration Architecture

### 5.1 Service Integration Pattern

```python
# Abstract AI Service Interface
class AIService(ABC):
    @abstractmethod
    async def generate(self, input_data: Dict) -> Dict:
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        pass
    
    @abstractmethod
    def estimate_cost(self, input_data: Dict) -> float:
        pass

# Service Implementations
class OpenAIService(AIService):
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.rate_limiter = RateLimiter(calls=50, period=60)
    
    async def generate(self, input_data: Dict) -> Dict:
        # Implementation with retry logic
        pass

class RunwayMLService(AIService):
    def __init__(self):
        self.client = RunwayML(api_key=settings.RUNWAY_API_KEY)
        self.circuit_breaker = CircuitBreaker(failure_threshold=5)
    
    async def generate(self, input_data: Dict) -> Dict:
        # Implementation with circuit breaker
        pass
```

### 5.2 Job Queue Architecture

```yaml
Queue System (Redis + Celery):
  Queues:
    - high_priority: User-initiated tasks
    - generation: AI generation tasks
    - processing: Media processing
    - export: Final rendering
    - notifications: Email/webhook

  Workers:
    - AI Workers: 4 instances (GPU)
    - Processing Workers: 8 instances
    - Export Workers: 2 instances
    - Notification Workers: 2 instances

  Task Examples:
    - generate_image_task
    - generate_audio_task
    - generate_video_task
    - process_storyboard_task
    - render_final_video_task
```

### 5.3 Cost Optimization

```python
class CostOptimizer:
    def __init__(self):
        self.usage_tracker = UsageTracker()
        self.cache_manager = CacheManager()
        
    def optimize_image_generation(self, prompt: str) -> Dict:
        # Check cache first
        cached = self.cache_manager.get(prompt)
        if cached:
            return cached
            
        # Check similar prompts
        similar = self.find_similar_prompts(prompt)
        if similar:
            return self.modify_cached_result(similar)
            
        # Optimize prompt for cost
        optimized = self.optimize_prompt(prompt)
        
        # Select cheapest provider
        provider = self.select_provider(optimized)
        
        return {
            'provider': provider,
            'prompt': optimized,
            'estimated_cost': provider.estimate_cost(optimized)
        }
```

---

## 6. Security Architecture

### 6.1 Authentication & Authorization

```yaml
Authentication:
  Provider: Auth0 / AWS Cognito
  Methods:
    - OAuth 2.0 (Google, GitHub)
    - Email/Password
    - Magic Links
  
  Token Management:
    - Access Token: 15 minutes
    - Refresh Token: 7 days
    - Session: Redis storage

Authorization:
  Model: RBAC (Role-Based Access Control)
  Roles:
    - viewer: Read-only access
    - editor: Create/edit content
    - admin: Full project control
    - owner: Billing and settings
```

### 6.2 API Security

```yaml
Security Measures:
  1. API Gateway:
     - Rate limiting: 100 req/min per user
     - API key validation
     - Request signing (HMAC)
     
  2. Input Validation:
     - Joi/Zod schemas
     - SQL injection prevention
     - XSS protection
     
  3. File Upload:
     - Virus scanning (ClamAV)
     - File type validation
     - Size limits enforced
     
  4. Secrets Management:
     - AWS Secrets Manager
     - Environment isolation
     - Key rotation policy
```

### 6.3 Data Protection

```yaml
Encryption:
  At Rest:
    - Database: AES-256
    - S3: SSE-S3
    - Backups: Encrypted
    
  In Transit:
    - TLS 1.3 minimum
    - Certificate pinning
    - HSTS enabled

Privacy:
  - GDPR compliance
  - Data minimization
  - Right to deletion
  - Audit logging
```

---

## 7. Infrastructure Architecture

### 7.1 AWS Infrastructure

```yaml
Compute:
  - EKS Cluster: Kubernetes 1.27
  - Node Groups:
    - General: t3.medium (2-10 nodes)
    - GPU: g4dn.xlarge (1-5 nodes)
  - Fargate: Serverless tasks

Storage:
  - S3 Buckets:
    - media-assets: User uploads
    - generated-content: AI outputs
    - exports: Final videos
  - EFS: Shared storage for processing

Database:
  - RDS PostgreSQL: Multi-AZ
  - ElastiCache Redis: Cluster mode
  - DynamoDB: Session storage

Networking:
  - VPC: 3 AZs
  - Private subnets: Backend services
  - Public subnets: Load balancers
  - NAT Gateway: Outbound traffic
```

### 7.2 Deployment Architecture

```yaml
CI/CD Pipeline:
  1. Source Control:
     - GitHub repositories
     - Branch protection rules
     - PR reviews required
     
  2. Build Pipeline:
     - GitHub Actions
     - Docker image builds
     - Security scanning
     - Unit tests
     
  3. Deployment:
     - ArgoCD for Kubernetes
     - Blue-green deployments
     - Automated rollbacks
     - Health checks
     
  4. Monitoring:
     - Datadog APM
     - CloudWatch logs
     - Prometheus metrics
     - PagerDuty alerts
```

### 7.3 Scaling Strategy

```yaml
Horizontal Scaling:
  - Auto-scaling groups
  - Kubernetes HPA
  - Load balancer distribution
  
Vertical Scaling:
  - GPU instances for AI
  - Memory-optimized for cache
  - Compute-optimized for processing

Performance Targets:
  - Response time: p95 < 200ms
  - Throughput: 10,000 req/sec
  - Availability: 99.9%
  - RTO: 15 minutes
  - RPO: 1 hour
```

---

## 8. Monitoring & Observability

### 8.1 Metrics & Monitoring

```yaml
Application Metrics:
  - Request rate
  - Error rate
  - Response time
  - Queue depth
  - Generation success rate
  
Business Metrics:
  - Videos created
  - API usage by service
  - Cost per video
  - User engagement
  
Infrastructure Metrics:
  - CPU/Memory usage
  - Disk I/O
  - Network throughput
  - Container health
```

### 8.2 Logging Architecture

```yaml
Log Pipeline:
  1. Collection:
     - Fluentd/Fluent Bit
     - Structured JSON logs
     - Correlation IDs
     
  2. Processing:
     - AWS Kinesis
     - Log parsing
     - Enrichment
     
  3. Storage:
     - CloudWatch Logs
     - S3 for archives
     - 30-day retention
     
  4. Analysis:
     - CloudWatch Insights
     - Datadog Log Management
     - Alert generation
```

### 8.3 Distributed Tracing

```yaml
Tracing Setup:
  - OpenTelemetry SDK
  - Jaeger backend
  - Service mesh integration
  - Correlation with logs

Key Traces:
  - End-to-end generation flow
  - API gateway to services
  - External API calls
  - Database queries
```

---

## 9. Disaster Recovery

### 9.1 Backup Strategy

```yaml
Backup Schedule:
  Database:
    - Full: Daily at 2 AM UTC
    - Incremental: Every 6 hours
    - Retention: 30 days
    
  Media Files:
    - S3 versioning enabled
    - Cross-region replication
    - Lifecycle policies
    
  Configuration:
    - Git repositories
    - Secrets backup
    - Infrastructure as Code
```

### 9.2 Recovery Procedures

```yaml
RTO/RPO Targets:
  - Critical Services: RTO 15min, RPO 1hr
  - Non-critical: RTO 4hr, RPO 4hr
  
Recovery Plans:
  1. Database failure:
     - Automated failover to replica
     - Point-in-time recovery
     
  2. Service outage:
     - Kubernetes auto-recovery
     - Multi-region failover
     
  3. Data corruption:
     - Restore from backups
     - Audit trail replay
```

---

## 10. Technology Decisions

### 10.1 Technology Choices Rationale

| Technology | Choice | Rationale |
|------------|--------|-----------|
| Frontend Framework | Next.js 14 | SSR, performance, ecosystem |
| Backend Language | Node.js + Python | JS for web, Python for AI |
| Database | PostgreSQL | ACID, JSON support, maturity |
| Cache | Redis | Performance, data structures |
| Message Queue | Redis + Celery | Simplicity, Python support |
| Container Runtime | Docker | Industry standard |
| Orchestration | Kubernetes | Scalability, flexibility |
| Cloud Provider | AWS | Service breadth, ML tools |
| CDN | CloudFront | AWS integration, performance |
| Monitoring | Datadog | Full-stack observability |

### 10.2 Future Technology Considerations

- **GraphQL**: For flexible API queries
- **WebAssembly**: For browser-based video processing
- **Edge Computing**: For global latency reduction
- **Blockchain**: For content ownership/licensing
- **WebRTC**: For real-time collaboration

---

## 11. Development Guidelines

### 11.1 Code Organization

```
Repository Structure:
evergreen/
├── services/
│   ├── project-service/
│   ├── script-service/
│   ├── media-service/
│   ├── ai-orchestrator/
│   └── video-editor/
├── packages/
│   ├── shared-types/
│   ├── common-utils/
│   └── api-client/
├── web/
├── mobile/ (future)
├── infrastructure/
│   ├── kubernetes/
│   ├── terraform/
│   └── scripts/
└── docs/
```

### 11.2 API Design Principles

```yaml
RESTful Design:
  - Resource-based URLs
  - HTTP methods for actions
  - Consistent naming
  - HATEOAS where applicable

Response Format:
  {
    "data": {},
    "meta": {
      "timestamp": "2025-07-22T10:00:00Z",
      "version": "1.0"
    },
    "errors": []
  }

Versioning:
  - URL path: /api/v1/
  - Header: X-API-Version
  - Deprecation warnings
```

### 11.3 Testing Strategy

```yaml
Test Pyramid:
  Unit Tests: 70%
    - Jest for JavaScript
    - Pytest for Python
    - Mock external deps
    
  Integration Tests: 20%
    - API endpoint tests
    - Service interaction
    - Database tests
    
  E2E Tests: 10%
    - Critical user flows
    - Cypress for frontend
    - Production-like env
    
Coverage Targets:
  - Overall: 85%
  - Critical paths: 95%
  - New code: 90%
```

---

## 12. Migration & Adoption

### 12.1 Migration Strategy

```yaml
Phase 1: MVP (Months 1-2)
  - Core functionality
  - Single region deployment
  - Beta user onboarding
  
Phase 2: Scale (Months 3-4)
  - Multi-region deployment
  - Performance optimization
  - Open registration
  
Phase 3: Enterprise (Months 5-6)
  - SSO integration
  - Advanced security
  - SLA guarantees
```

### 12.2 Adoption Plan

```yaml
Technical Adoption:
  - Comprehensive API docs
  - SDK development
  - Integration guides
  - Sample projects
  
User Adoption:
  - Onboarding tutorials
  - Template library
  - Community forums
  - Video guides
```

---

## 13. Appendices

### A. API Endpoint Reference
[See detailed API documentation]

### B. Database Migrations
[See migration scripts in /infrastructure/migrations]

### C. Security Audit Checklist
[See security documentation]

### D. Performance Benchmarks
[See performance test results]

---

**Document Sign-off**

| Role | Name | Date | Approval |
|------|------|------|----------|
| System Architect | | | |
| Tech Lead | | | |
| Security Lead | | | |
| DevOps Lead | | | |