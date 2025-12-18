# 🍌 Nano Banana Studio Pro - Code Quality Standards

> **Comprehensive Technical Documentation for Development Best Practices**  
> Version 1.0 | December 2025

---

## 📋 Table of Contents

- [Overview](#overview)
- [Code Style Guidelines](#code-style-guidelines)
- [Event Handling Best Practices](#event-handling-best-practices)
- [Error Handling & Debugging](#error-handling--debugging)
- [Automated Quality Tools](#automated-quality-tools)
- [Testing Standards](#testing-standards)
- [Maintenance Procedures](#maintenance-procedures)

---

## Overview

This document defines the coding standards, best practices, and maintenance procedures for Nano Banana Studio Pro. Following these guidelines ensures consistent, maintainable, and high-quality code.

### Quality Framework Components

| Component | Purpose | Location |
|-----------|---------|----------|
| **ESLint Config** | JavaScript/React linting | `scripts/code-quality/eslint.config.js` |
| **Auto-Repair Script** | Automated issue detection & fixing | `scripts/code-quality/auto-repair.ps1` |
| **Event Handler Audit** | UI interaction validation | `scripts/code-quality/event-handler-audit.js` |
| **Debug Helper** | Enhanced error feedback | `scripts/code-quality/debug-helper.py` |

---

## Code Style Guidelines

### Python Standards

```python
# ✅ GOOD: Use type hints and docstrings
async def process_video(
    video_path: Path,
    options: VideoOptions
) -> ProcessResult:
    """
    Process a video file with the given options.
    
    Args:
        video_path: Path to the input video file
        options: Processing configuration
        
    Returns:
        ProcessResult containing output path and metadata
        
    Raises:
        FileNotFoundError: If video_path doesn't exist
        VideoProcessingError: If processing fails
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    # Processing logic...
    return ProcessResult(output_path=output, metadata=meta)


# ❌ BAD: No type hints, no docstring, bare except
def process_video(path, opts):
    try:
        # processing...
        pass
    except:
        print("Error!")
        return None
```

### JavaScript/React Standards

```jsx
// ✅ GOOD: Proper event handling with error boundaries
function SceneCard({ scene, onApprove, onReject }) {
  const handleApprove = useCallback(async (e) => {
    e.stopPropagation()  // Prevent parent click
    try {
      await onApprove(scene.id)
    } catch (error) {
      console.error('Failed to approve scene:', error)
      // Show user-friendly error message
    }
  }, [scene.id, onApprove])

  return (
    <div 
      onClick={() => setSelected(scene.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === 'Enter' && setSelected(scene.id)}
    >
      <button 
        type="button"
        onClick={handleApprove}
        aria-label={`Approve scene ${scene.index}`}
      >
        Approve
      </button>
    </div>
  )
}

// ❌ BAD: Missing accessibility, inline handlers, no error handling
function SceneCard({ scene, onApprove }) {
  return (
    <div onClick={() => setSelected(scene.id)}>
      <button onClick={() => onApprove(scene.id)}>
        Approve
      </button>
    </div>
  )
}
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| **Python functions** | snake_case | `process_video()` |
| **Python classes** | PascalCase | `VideoProcessor` |
| **Python constants** | UPPER_SNAKE | `MAX_RETRIES` |
| **JS/React components** | PascalCase | `SceneCard` |
| **JS functions** | camelCase | `handleClick()` |
| **JS constants** | UPPER_SNAKE | `API_BASE_URL` |
| **CSS classes** | kebab-case | `scene-card-active` |

---

## Event Handling Best Practices

### Required Patterns

#### 1. Always Use `stopPropagation` for Nested Clickables

```jsx
// When a clickable element is inside another clickable element
<div onClick={handleParentClick}>
  <button onClick={(e) => {
    e.stopPropagation()  // ← Required!
    handleButtonClick()
  }}>
    Click Me
  </button>
</div>
```

#### 2. Always Handle Errors in Async Event Handlers

```jsx
const handleSubmit = async (e) => {
  e.preventDefault()
  
  try {
    setLoading(true)
    await api.submitForm(data)
    showSuccess('Form submitted!')
  } catch (error) {
    console.error('Submit failed:', error)
    showError(error.message || 'Submission failed')
  } finally {
    setLoading(false)
  }
}
```

#### 3. Add Keyboard Support for Clickable Non-Buttons

```jsx
<div
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick()
    }
  }}
  role="button"
  tabIndex={0}
  aria-label="Description of action"
>
  Clickable Div
</div>
```

#### 4. Use `useCallback` for Event Handlers Passed as Props

```jsx
// ✅ GOOD: Memoized callback prevents unnecessary re-renders
const handleApprove = useCallback((sceneId) => {
  api.approveScene(projectId, sceneId)
}, [projectId])

return <SceneList onApprove={handleApprove} />

// ❌ BAD: Creates new function on every render
return <SceneList onApprove={(id) => api.approveScene(projectId, id)} />
```

### Event Handler Checklist

- [ ] All buttons have explicit `type` attribute (`button` or `submit`)
- [ ] Nested clickables use `stopPropagation()`
- [ ] Async handlers have try/catch blocks
- [ ] Non-button clickables have keyboard support
- [ ] All interactive elements have appropriate ARIA attributes
- [ ] Event handlers are memoized with `useCallback` when passed as props

---

## Error Handling & Debugging

### Python Error Handling

```python
from scripts.code_quality.debug_helper import debug_exception

async def process_request(request: Request):
    try:
        result = await some_operation()
        return {"success": True, "data": result}
    
    except ValidationError as e:
        # Known error - handle gracefully
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except ExternalAPIError as e:
        # External service error
        logger.error(f"External API failed: {e}")
        raise HTTPException(status_code=502, detail="External service unavailable")
    
    except Exception as e:
        # Unknown error - use debug helper for analysis
        analysis = debug_exception(e, context="process_request")
        logger.error(f"Unexpected error: {analysis.message}")
        raise HTTPException(status_code=500, detail="Internal error")
```

### JavaScript Error Handling

```jsx
// API calls should always have error handling
async function fetchData() {
  try {
    const response = await api.getData()
    setData(response)
  } catch (error) {
    // Log for debugging
    console.error('API Error:', error)
    
    // Show user-friendly message
    if (error.response?.status === 401) {
      showError('Please log in to continue')
    } else if (error.response?.status === 404) {
      showError('Resource not found')
    } else {
      showError('Something went wrong. Please try again.')
    }
  }
}
```

### Debug Helper Usage

```python
# Import the debug helper
from scripts.code_quality.debug_helper import (
    debug_exception,
    get_debug_helper,
    install_exception_hook
)

# Option 1: Manual error logging
try:
    risky_operation()
except Exception as e:
    analysis = debug_exception(e, "context description")
    # analysis.suggested_fixes contains actionable fixes

# Option 2: Install global exception hook
install_exception_hook()  # All unhandled exceptions get analyzed
```

---

## Automated Quality Tools

### Running the Auto-Repair Script

```powershell
# Scan for issues (no changes)
.\scripts\code-quality\auto-repair.ps1

# Scan and auto-fix where possible
.\scripts\code-quality\auto-repair.ps1 -Fix

# Verbose output
.\scripts\code-quality\auto-repair.ps1 -Verbose
```

### Running the Event Handler Audit

```bash
# Audit frontend event handlers
node scripts/code-quality/event-handler-audit.js

# Audit specific directory
node scripts/code-quality/event-handler-audit.js ./frontend/src/components
```

### ESLint Integration

```bash
# Add to frontend/package.json
cd frontend
npm install eslint eslint-plugin-react eslint-plugin-react-hooks --save-dev

# Run linting
npx eslint src/ --ext .js,.jsx

# Auto-fix issues
npx eslint src/ --ext .js,.jsx --fix
```

### Pre-Commit Hook Setup

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

# Run auto-repair scan
powershell -File scripts/code-quality/auto-repair.ps1
if [ $? -ne 0 ]; then
    echo "Code quality issues found. Run with -Fix or fix manually."
    exit 1
fi

# Run event handler audit
node scripts/code-quality/event-handler-audit.js
if [ $? -ne 0 ]; then
    echo "Event handler issues found. Fix before committing."
    exit 1
fi

exit 0
```

---

## Testing Standards

### Unit Test Structure

```python
# tests/test_service.py
import pytest
from backend.services.face_service import FaceService

class TestFaceService:
    @pytest.fixture
    def service(self):
        return FaceService(use_gpu=False)
    
    def test_detect_faces_returns_list(self, service, sample_image):
        """Face detection should return a list of detections."""
        result = service.detect_faces(sample_image)
        assert isinstance(result, list)
    
    def test_detect_faces_with_no_face(self, service, no_face_image):
        """Should return empty list when no faces found."""
        result = service.detect_faces(no_face_image)
        assert result == []
    
    @pytest.mark.asyncio
    async def test_async_operation(self, service):
        """Async operations should complete successfully."""
        result = await service.async_method()
        assert result is not None
```

### React Component Testing

```jsx
// tests/SceneCard.test.jsx
import { render, fireEvent, screen } from '@testing-library/react'
import SceneCard from '../src/components/SceneCard'

describe('SceneCard', () => {
  const mockScene = { index: 1, status: 'ready', prompt: 'Test' }
  const mockOnApprove = jest.fn()
  
  beforeEach(() => {
    jest.clearAllMocks()
  })
  
  it('calls onApprove when approve button clicked', () => {
    render(<SceneCard scene={mockScene} onApprove={mockOnApprove} />)
    
    fireEvent.click(screen.getByRole('button', { name: /approve/i }))
    
    expect(mockOnApprove).toHaveBeenCalledWith(1)
  })
  
  it('stops propagation on button click', () => {
    const mockParentClick = jest.fn()
    render(
      <div onClick={mockParentClick}>
        <SceneCard scene={mockScene} onApprove={mockOnApprove} />
      </div>
    )
    
    fireEvent.click(screen.getByRole('button', { name: /approve/i }))
    
    expect(mockParentClick).not.toHaveBeenCalled()
  })
})
```

### Test Coverage Requirements

| Component | Minimum Coverage |
|-----------|------------------|
| Backend Services | 80% |
| API Endpoints | 90% |
| Frontend Components | 70% |
| Utility Functions | 95% |

---

## Maintenance Procedures

### Daily Checks

1. Run auto-repair scan on modified files
2. Review debug logs for recurring errors
3. Check API response times

### Weekly Checks

1. Full codebase quality scan
2. Dependency update check
3. Performance profiling
4. Log rotation and cleanup

### Pre-Release Checklist

- [ ] All tests passing
- [ ] Auto-repair scan clean (no errors)
- [ ] Event handler audit clean
- [ ] ESLint clean (no errors, warnings reviewed)
- [ ] Debug helper integrated for new features
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

### Emergency Debugging

```bash
# 1. Enable verbose logging
export LOG_LEVEL=DEBUG

# 2. Run with debug helper
python -c "
from scripts.code_quality.debug_helper import install_exception_hook
install_exception_hook()
# Now run your code
"

# 3. Check debug logs
tail -f data/debug.log

# 4. Review structured error log
cat data/debug.json | jq '.[-5:]'
```

---

## Quick Reference

### Commands

| Task | Command |
|------|---------|
| Quality scan | `.\scripts\code-quality\auto-repair.ps1` |
| Auto-fix | `.\scripts\code-quality\auto-repair.ps1 -Fix` |
| Event audit | `node scripts/code-quality/event-handler-audit.js` |
| Lint frontend | `cd frontend && npx eslint src/` |
| Run tests | `pytest tests/ -v` |
| Test coverage | `pytest tests/ --cov=backend` |

### File Locations

```
scripts/code-quality/
├── eslint.config.js       # ESLint configuration
├── auto-repair.ps1        # Automated repair script
├── event-handler-audit.js # Event handler validation
└── debug-helper.py        # Enhanced debugging system

docs/
└── CODE_QUALITY_STANDARDS.md  # This document
```

---

*Nano Banana Studio Pro - Quality First* 🍌✨
