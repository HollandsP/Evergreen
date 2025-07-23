# Contributing to Evergreen

We love your input! We want to make contributing to Evergreen as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with Github
We use Github to host code, to track issues and feature requests, as well as accept pull requests.

## Development Process
We use [Github Flow](https://guides.github.com/introduction/flow/index.html), so all code changes happen through Pull Requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Any contributions you make will be under the MIT Software License
In short, when you submit code changes, your submissions are understood to be under the same [MIT License](http://choosealicense.com/licenses/mit/) that covers the project. Feel free to contact the maintainers if that's a concern.

## Report bugs using Github's [issues](https://github.com/yourusername/evergreen/issues)
We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/yourusername/evergreen/issues/new); it's that easy!

## Write bug reports with detail, background, and sample code

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

## Development Setup

### Prerequisites
- Node.js 18+
- Python 3.9+
- PostgreSQL 14+
- Redis 6+
- FFmpeg

### Setup Steps
1. Clone the repository
```bash
git clone https://github.com/yourusername/evergreen.git
cd evergreen
```

2. Install dependencies
```bash
# Frontend
cd web && npm install

# Backend
cd ../api && pip install -r requirements.txt
```

3. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. Initialize the database
```bash
npm run db:init
```

5. Start development servers
```bash
npm run dev
```

## Code Style

### Python
- Follow PEP 8
- Use type hints
- Write docstrings for all public functions
- Use `black` for formatting
- Use `flake8` for linting

### TypeScript/JavaScript
- Use TypeScript for all new code
- Follow the existing ESLint configuration
- Use Prettier for formatting
- Write JSDoc comments for complex functions

### Git Commit Messages
- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Examples:
```
feat: Add script parsing endpoint
fix: Resolve memory leak in video processing
docs: Update API documentation for v1.1
test: Add integration tests for voice synthesis
refactor: Optimize database queries for performance
```

## Testing

### Running Tests
```bash
# All tests
npm test

# Frontend tests
cd web && npm test

# Backend tests
cd api && pytest

# E2E tests
npm run test:e2e
```

### Writing Tests
- Write unit tests for all new functions
- Write integration tests for API endpoints
- Aim for >80% code coverage
- Use meaningful test names that describe what is being tested

## Documentation

- Update the README.md with details of changes to the interface
- Update the API documentation for any endpoint changes
- Comment your code where necessary
- Update type definitions

## Pull Request Process

1. Update the README.md with details of changes to the interface
2. Update the CHANGELOG.md with a note describing your changes
3. The PR will be merged once you have the sign-off of at least one maintainer

## Community

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## Questions?

Feel free to open an issue with the label "question" or reach out to the maintainers directly.

Thank you for contributing to Evergreen! 🌲