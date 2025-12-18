"""
Enhanced Debugging System for Nano Banana Studio Pro
=====================================================
Provides meaningful feedback and suggested fixes for common errors.
Implements enhanced debugging per Global Rules requirements.

Usage:
    python debug-helper.py [--watch] [--log-file PATH]
"""

import sys
import os
import re
import json
import traceback
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ErrorCategory(Enum):
    IMPORT = "import_error"
    TYPE = "type_error"
    VALUE = "value_error"
    KEY = "key_error"
    ATTRIBUTE = "attribute_error"
    CONNECTION = "connection_error"
    FILE = "file_error"
    API = "api_error"
    VALIDATION = "validation_error"
    UNKNOWN = "unknown"


@dataclass
class ErrorAnalysis:
    """Structured error analysis with suggested fixes."""
    category: ErrorCategory
    message: str
    file: Optional[str]
    line: Optional[int]
    context: Optional[str]
    suggested_fixes: List[str]
    documentation_links: List[str]
    severity: str  # critical, high, medium, low


# Common error patterns and their solutions
ERROR_PATTERNS: Dict[str, Dict[str, Any]] = {
    # Import Errors
    r"ModuleNotFoundError: No module named '(\w+)'": {
        "category": ErrorCategory.IMPORT,
        "fixes": [
            "Install the missing module: pip install {0}",
            "Check if the module name is correct",
            "Verify your virtual environment is activated",
            "Check requirements.txt includes the package"
        ],
        "docs": ["https://pip.pypa.io/en/stable/user_guide/"]
    },
    r"ImportError: cannot import name '(\w+)' from '(\w+)'": {
        "category": ErrorCategory.IMPORT,
        "fixes": [
            "Check if '{0}' exists in module '{1}'",
            "The API may have changed - check documentation",
            "Try: from {1} import {0} as alias",
            "Upgrade the package: pip install --upgrade {1}"
        ],
        "docs": []
    },
    
    # Type Errors
    r"TypeError: '(\w+)' object is not (callable|subscriptable|iterable)": {
        "category": ErrorCategory.TYPE,
        "fixes": [
            "Check the type of the object - it's a {0}, not what you expected",
            "Look for typos in variable names",
            "Ensure the function/method returns the expected type",
            "Add type hints to catch this at development time"
        ],
        "docs": ["https://docs.python.org/3/library/typing.html"]
    },
    r"TypeError: (\w+)\(\) got an unexpected keyword argument '(\w+)'": {
        "category": ErrorCategory.TYPE,
        "fixes": [
            "Remove or rename the argument '{1}' from {0}() call",
            "Check the function signature: help({0})",
            "The API may have changed - verify parameter names",
            "Use **kwargs if passing dynamic parameters"
        ],
        "docs": []
    },
    r"TypeError: (\w+)\(\) missing (\d+) required positional argument": {
        "category": ErrorCategory.TYPE,
        "fixes": [
            "Add the missing {1} argument(s) to {0}()",
            "Check the function signature for required parameters",
            "Consider if default values should be added"
        ],
        "docs": []
    },
    
    # Key Errors
    r"KeyError: '(\w+)'": {
        "category": ErrorCategory.KEY,
        "fixes": [
            "Key '{0}' doesn't exist in the dictionary",
            "Use .get('{0}', default_value) to avoid this error",
            "Check available keys with: dict.keys()",
            "Verify the data structure matches expectations"
        ],
        "docs": []
    },
    
    # Attribute Errors
    r"AttributeError: '(\w+)' object has no attribute '(\w+)'": {
        "category": ErrorCategory.ATTRIBUTE,
        "fixes": [
            "'{0}' type doesn't have '{1}' attribute",
            "Check if the object is None: add null check",
            "Verify the object type: type(obj)",
            "Look for typos in the attribute name"
        ],
        "docs": []
    },
    
    # Connection Errors
    r"ConnectionRefusedError": {
        "category": ErrorCategory.CONNECTION,
        "fixes": [
            "Ensure the target service is running",
            "Check the host and port are correct",
            "Verify firewall settings allow the connection",
            "Check Docker containers are up: docker-compose ps"
        ],
        "docs": []
    },
    r"httpx\.(ConnectError|TimeoutException)": {
        "category": ErrorCategory.CONNECTION,
        "fixes": [
            "Verify the API endpoint URL is correct",
            "Check if the service is running and accessible",
            "Increase timeout if dealing with slow operations",
            "Check network connectivity"
        ],
        "docs": []
    },
    
    # File Errors
    r"FileNotFoundError: \[Errno 2\] No such file or directory: '(.+)'": {
        "category": ErrorCategory.FILE,
        "fixes": [
            "File not found: {0}",
            "Check if the path is correct (absolute vs relative)",
            "Ensure the file exists: Path('{0}').exists()",
            "Check working directory: os.getcwd()"
        ],
        "docs": []
    },
    r"PermissionError: \[Errno 13\] Permission denied: '(.+)'": {
        "category": ErrorCategory.FILE,
        "fixes": [
            "No permission to access: {0}",
            "Check file permissions: ls -la {0}",
            "Run with appropriate privileges",
            "Check if file is locked by another process"
        ],
        "docs": []
    },
    
    # Validation Errors (Pydantic)
    r"pydantic.*ValidationError": {
        "category": ErrorCategory.VALIDATION,
        "fixes": [
            "Request data doesn't match the expected schema",
            "Check required fields are provided",
            "Verify data types match schema definitions",
            "Review the Pydantic model for field requirements"
        ],
        "docs": ["https://docs.pydantic.dev/latest/"]
    },
    
    # FastAPI Errors
    r"HTTPException.*status_code=(\d+)": {
        "category": ErrorCategory.API,
        "fixes": [
            "API returned HTTP {0} error",
            "Check request parameters and body",
            "Verify authentication if required",
            "Review API documentation for endpoint requirements"
        ],
        "docs": ["https://fastapi.tiangolo.com/tutorial/handling-errors/"]
    },
}


class DebugHelper:
    """Enhanced debugging assistant with intelligent error analysis."""
    
    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file or PROJECT_ROOT / "data" / "debug.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger("debug-helper")
    
    def analyze_error(self, error: Exception, context: Optional[str] = None) -> ErrorAnalysis:
        """Analyze an exception and provide actionable feedback."""
        error_str = str(error)
        error_type = type(error).__name__
        tb = traceback.extract_tb(error.__traceback__)
        
        # Get file and line info
        file_info = None
        line_info = None
        if tb:
            last_frame = tb[-1]
            file_info = last_frame.filename
            line_info = last_frame.lineno
        
        # Match against known patterns
        for pattern, info in ERROR_PATTERNS.items():
            match = re.search(pattern, f"{error_type}: {error_str}")
            if match:
                groups = match.groups()
                fixes = [f.format(*groups) for f in info["fixes"]]
                
                return ErrorAnalysis(
                    category=info["category"],
                    message=str(error),
                    file=file_info,
                    line=line_info,
                    context=context,
                    suggested_fixes=fixes,
                    documentation_links=info.get("docs", []),
                    severity=self._determine_severity(info["category"])
                )
        
        # Unknown error
        return ErrorAnalysis(
            category=ErrorCategory.UNKNOWN,
            message=str(error),
            file=file_info,
            line=line_info,
            context=context,
            suggested_fixes=[
                f"Error type: {error_type}",
                "Check the stack trace for more details",
                "Search for the error message online",
                "Review recent code changes"
            ],
            documentation_links=[],
            severity="medium"
        )
    
    def _determine_severity(self, category: ErrorCategory) -> str:
        """Determine error severity based on category."""
        critical = [ErrorCategory.CONNECTION, ErrorCategory.FILE]
        high = [ErrorCategory.IMPORT, ErrorCategory.API]
        medium = [ErrorCategory.TYPE, ErrorCategory.KEY, ErrorCategory.ATTRIBUTE]
        
        if category in critical:
            return "critical"
        elif category in high:
            return "high"
        elif category in medium:
            return "medium"
        return "low"
    
    def format_analysis(self, analysis: ErrorAnalysis) -> str:
        """Format error analysis for display."""
        lines = [
            "",
            "=" * 60,
            f" DEBUG ANALYSIS - {analysis.category.value.upper()}",
            "=" * 60,
            "",
            f"Severity: {analysis.severity.upper()}",
            f"Error: {analysis.message}",
        ]
        
        if analysis.file:
            lines.append(f"File: {analysis.file}:{analysis.line or '?'}")
        
        if analysis.context:
            lines.append(f"Context: {analysis.context}")
        
        lines.extend([
            "",
            "SUGGESTED FIXES:",
        ])
        
        for i, fix in enumerate(analysis.suggested_fixes, 1):
            lines.append(f"  {i}. {fix}")
        
        if analysis.documentation_links:
            lines.extend([
                "",
                "DOCUMENTATION:",
            ])
            for link in analysis.documentation_links:
                lines.append(f"  - {link}")
        
        lines.extend(["", "=" * 60, ""])
        
        return "\n".join(lines)
    
    def log_error(self, error: Exception, context: Optional[str] = None):
        """Log error with full analysis."""
        analysis = self.analyze_error(error, context)
        formatted = self.format_analysis(analysis)
        
        self.logger.error(formatted)
        
        # Also save to JSON for programmatic access
        json_log = self.log_file.with_suffix('.json')
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "analysis": asdict(analysis)
        }
        log_entry["analysis"]["category"] = analysis.category.value
        
        # Append to JSON log
        entries = []
        if json_log.exists():
            try:
                entries = json.loads(json_log.read_text())
            except:
                pass
        entries.append(log_entry)
        
        # Keep last 1000 entries
        entries = entries[-1000:]
        json_log.write_text(json.dumps(entries, indent=2))
        
        return analysis


# Global debug helper instance
_debug_helper: Optional[DebugHelper] = None

def get_debug_helper() -> DebugHelper:
    """Get or create debug helper instance."""
    global _debug_helper
    if _debug_helper is None:
        _debug_helper = DebugHelper()
    return _debug_helper


def debug_exception(error: Exception, context: Optional[str] = None) -> ErrorAnalysis:
    """Convenience function to analyze and log an exception."""
    helper = get_debug_helper()
    analysis = helper.log_error(error, context)
    print(helper.format_analysis(analysis))
    return analysis


# Exception hook for unhandled exceptions
def enhanced_exception_hook(exc_type, exc_value, exc_traceback):
    """Enhanced exception hook that provides debugging assistance."""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    helper = get_debug_helper()
    error = exc_value
    error.__traceback__ = exc_traceback
    analysis = helper.log_error(error, "Unhandled exception")
    print(helper.format_analysis(analysis))


def install_exception_hook():
    """Install the enhanced exception hook."""
    sys.excepthook = enhanced_exception_hook


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced Debugging System")
    parser.add_argument("--watch", action="store_true", help="Watch for new errors")
    parser.add_argument("--log-file", type=Path, help="Log file path")
    parser.add_argument("--test", action="store_true", help="Run test errors")
    args = parser.parse_args()
    
    if args.test:
        print("Testing debug helper with sample errors...")
        print("")
        
        # Test various error types
        test_errors = [
            ModuleNotFoundError("No module named 'nonexistent'"),
            KeyError("missing_key"),
            TypeError("'NoneType' object is not subscriptable"),
            FileNotFoundError("[Errno 2] No such file or directory: '/path/to/file'"),
        ]
        
        helper = DebugHelper(args.log_file)
        
        for error in test_errors:
            analysis = helper.analyze_error(error, "Test context")
            print(helper.format_analysis(analysis))
    else:
        print("Debug Helper initialized. Import and use:")
        print("  from scripts.code_quality.debug_helper import debug_exception")
        print("  debug_exception(error, 'context')")
