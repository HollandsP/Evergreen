# Evergreen Video Production Pipeline - Test Suite

## Overview

This comprehensive test suite ensures the reliability and correctness of the Evergreen video production pipeline. The tests cover unit testing, integration testing, API endpoints, WebSocket communication, and error handling.

## Test Structure

```
tests/
├── api/                    # API endpoint tests
│   └── endpoints.test.ts   # Tests for all API routes
├── components/             # Component tests
│   └── stages.test.tsx     # Tests for stage components
├── fixtures/               # Test data
│   └── test-script.txt     # Sample script for testing
├── integration/            # Integration tests
│   ├── pipeline.test.ts    # End-to-end pipeline tests
│   ├── websocket.test.ts   # WebSocket communication tests
│   └── error-handling.test.tsx  # Error boundary and edge cases
├── mocks/                  # Mock implementations
│   └── handlers.ts         # MSW mock handlers
├── utils/                  # Test utilities
│   └── test-helpers.ts     # Helper functions for tests
├── setup.ts               # Jest setup and global mocks
└── README.md              # This file
```

## Running Tests

### All Tests
```bash
npm test
```

### Watch Mode (for development)
```bash
npm test:watch
```

### With Coverage Report
```bash
npm test:coverage
```

### CI Mode (for pipelines)
```bash
npm test:ci
```

## Test Categories

### 1. Integration Tests (`integration/pipeline.test.ts`)
Tests the complete flow from script upload to final video export:
- Script parsing and scene extraction
- Voice selection
- Audio generation for all scenes
- Image generation with DALL-E 3
- Video generation with audio synchronization
- Final assembly and export
- State persistence across reloads
- Error recovery mechanisms

### 2. Component Tests (`components/stages.test.tsx`)
Tests individual stage components:
- ScriptProcessor: File upload, parsing, scene editing
- AudioGenerator: Batch generation, progress tracking
- ImageGenerator: DALL-E 3 integration, image uploads
- VideoGenerator: Provider selection, audio sync
- FinalAssembly: Timeline editing, export settings

### 3. API Endpoint Tests (`api/endpoints.test.ts`)
Tests all API routes:
- Request validation
- Error handling
- Response formats
- Rate limiting
- Batch operations
- File uploads

### 4. WebSocket Tests (`integration/websocket.test.ts`)
Tests real-time communication:
- Connection management
- Reconnection logic
- Event subscriptions
- Job progress updates
- Error notifications
- System status updates

### 5. Error Handling Tests (`integration/error-handling.test.tsx`)
Tests error scenarios and edge cases:
- Error boundaries
- Network failures
- State corruption recovery
- Memory management
- Concurrent operations
- Browser compatibility

## Test Utilities

### Mock Helpers (`utils/test-helpers.ts`)
- `createMockScene()`: Generate test scene data
- `createMockAudioData()`: Generate test audio data
- `createMockImageData()`: Generate test image data
- `setupTestState()`: Initialize test state
- `createMockWebSocket()`: Mock WebSocket connections
- `mockApiResponses`: Pre-configured API response mocks

### Setup (`setup.ts`)
Global test configuration:
- Jest DOM matchers
- TextEncoder/TextDecoder polyfills
- localStorage mock
- fetch mock
- IntersectionObserver mock
- Environment variables

## Coverage Requirements

The test suite aims for:
- **80%** branch coverage
- **80%** line coverage
- **80%** function coverage
- **80%** statement coverage

Run `npm test:coverage` to see current coverage metrics.

## Writing New Tests

### Component Test Example
```typescript
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MyComponent } from '@/components/MyComponent'

describe('MyComponent', () => {
  it('should handle user interaction', async () => {
    const user = userEvent.setup()
    render(<MyComponent />)
    
    const button = screen.getByRole('button', { name: /click me/i })
    await user.click(button)
    
    expect(screen.getByText(/clicked!/i)).toBeInTheDocument()
  })
})
```

### API Test Example
```typescript
import { createMocks } from 'node-mocks-http'
import handler from '@/pages/api/myEndpoint'

describe('/api/myEndpoint', () => {
  it('should return data', async () => {
    const { req, res } = createMocks({
      method: 'POST',
      body: { data: 'test' },
    })
    
    await handler(req, res)
    
    expect(res._getStatusCode()).toBe(200)
    expect(JSON.parse(res._getData())).toHaveProperty('success', true)
  })
})
```

### Integration Test Example
```typescript
import { productionState } from '@/lib/production-state'
import { mockApiResponses } from '@/tests/utils/test-helpers'

describe('Feature Integration', () => {
  it('should complete workflow', async () => {
    // Setup
    global.fetch = jest.fn()
      .mockResolvedValueOnce(mockApiResponses.scriptParse(scenes))
      .mockResolvedValueOnce(mockApiResponses.audioBatch(scenes))
    
    // Execute workflow
    await processScript(testScript)
    
    // Verify
    const state = productionState.getState()
    expect(state.script.status).toBe('completed')
    expect(state.audio.generatedAudio).toHaveLength(scenes.length)
  })
})
```

## Debugging Tests

### VSCode Debug Configuration
Add to `.vscode/launch.json`:
```json
{
  "type": "node",
  "request": "launch",
  "name": "Jest Debug",
  "program": "${workspaceFolder}/node_modules/.bin/jest",
  "args": ["--runInBand", "--no-cache", "${file}"],
  "console": "integratedTerminal",
  "internalConsoleOptions": "neverOpen"
}
```

### Common Issues

1. **Mock not working**: Ensure mocks are cleared between tests
   ```typescript
   beforeEach(() => {
     jest.clearAllMocks()
   })
   ```

2. **Async test failing**: Use `waitFor` for async assertions
   ```typescript
   await waitFor(() => {
     expect(screen.getByText(/loaded/i)).toBeInTheDocument()
   })
   ```

3. **State pollution**: Reset state before each test
   ```typescript
   beforeEach(() => {
     productionState.reset()
   })
   ```

## CI/CD Integration

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests
- Manual workflow dispatch

The CI pipeline:
1. Runs linting and type checking
2. Executes all tests with coverage
3. Uploads coverage to Codecov
4. Builds the application
5. Stores build artifacts

## Best Practices

1. **Test behavior, not implementation**: Focus on what the code does, not how
2. **Use descriptive test names**: Make it clear what's being tested
3. **Keep tests isolated**: Each test should be independent
4. **Mock external dependencies**: Don't make real API calls
5. **Test edge cases**: Include error scenarios and boundary conditions
6. **Maintain test data**: Keep fixtures up-to-date with schema changes
7. **Run tests before committing**: Ensure all tests pass locally

## Troubleshooting

### Tests failing locally but passing in CI
- Check Node.js version matches CI
- Ensure all dependencies are installed
- Clear Jest cache: `npx jest --clearCache`

### Coverage not meeting threshold
- Add tests for uncovered branches
- Check for unreachable code
- Review coverage report: `open coverage/lcov-report/index.html`

### Slow test execution
- Use `test.concurrent` for independent tests
- Mock heavy operations
- Optimize test setup/teardown

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure tests cover happy path and error cases
3. Update this README if adding new test patterns
4. Maintain or improve coverage metrics

## Resources

- [Jest Documentation](https://jestjs.io/docs/getting-started)
- [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Best Practices](https://github.com/goldbergyoni/javascript-testing-best-practices)
- [MSW Documentation](https://mswjs.io/docs/)