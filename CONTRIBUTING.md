# Contributing to Nano Banana Studio Pro

Thank you for your interest in contributing to Nano Banana Studio Pro! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please be respectful and constructive in all interactions. We're building something awesome together.

## Getting Started

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- FFmpeg
- Git

### Development Setup

```powershell
# Clone the repository
git clone https://github.com/your-repo/nano-banana-studio.git
cd nano-banana-studio

# Create virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
copy .env.example .env
# Edit .env with your API keys

# Run development server
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

## Development Workflow

### Branch Naming
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Test additions/updates

### Commit Messages
Follow conventional commits:
```
type(scope): description

feat(api): add new storyboard endpoint
fix(video): resolve ffmpeg timeout issue
docs(readme): update installation instructions
```

### Pull Request Process

1. Create a feature branch from `develop`
2. Make your changes
3. Run linting: `ruff check backend/`
4. Run tests: `pytest tests/ -v`
5. Update documentation if needed
6. Submit PR to `develop` branch

## Code Standards

### Python Style
- Follow PEP 8
- Use Black formatter (line length: 100)
- Use isort for imports
- Type hints encouraged

### Running Linters
```bash
# Format code
black backend/ tests/
isort backend/ tests/

# Check linting
ruff check backend/

# Type checking
mypy backend/ --ignore-missing-imports
```

### Testing
```bash
# Run all tests
pytest tests/ -v

# With coverage
pytest tests/ -v --cov=backend --cov-report=html

# Run specific test file
pytest tests/test_services.py -v
```

## Project Structure

```
nano-banana-studio/
├── backend/
│   ├── api/          # FastAPI application
│   ├── services/     # Core services
│   └── workers/      # Background workers
├── config/           # Configuration files
├── docs/             # Documentation
├── n8n/              # n8n workflows
├── scripts/          # Utility scripts
└── tests/            # Test suite
```

## Adding New Features

### New Service
1. Create service file in `backend/services/`
2. Follow existing patterns (singleton, async)
3. Add exports to `backend/services/__init__.py`
4. Add API endpoints in `backend/api/main.py`
5. Write tests in `tests/`
6. Update documentation

### New n8n Workflow
1. Create workflow JSON in `n8n/workflows/`
2. Follow naming convention: `XX_workflow_name.json`
3. Document webhook endpoints
4. Update workflow documentation

## Documentation

- Update README.md for major features
- Add to CHANGELOG.md following Keep a Changelog format
- Create/update docs/ files as needed

## Questions?

Open an issue for questions or discussions.

---

Thank you for contributing! 🍌
