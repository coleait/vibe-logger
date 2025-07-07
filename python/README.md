# VibeCoding Logger - Python Implementation

**AI-Native Logging for LLM Agent Development**

This is the Python implementation of VibeCoding Logger, a specialized logging library designed for AI-driven development where LLMs need rich, structured context to understand and debug code effectively.

## 🚀 Quick Start

### Installation

```bash
pip install vibelogger
```

### Basic Usage

```python
from vibelogger import create_file_logger

# Create logger with auto-save to timestamped file
logger = create_file_logger("my_project")

# Log with rich context for AI analysis
logger.info(
    operation="fetchUserProfile",
    message="Starting user profile fetch",
    context={"user_id": "123", "source": "api_endpoint"},
    human_note="AI-TODO: Check if user exists before fetching profile"
)

# Log exceptions with full context
try:
    result = risky_operation()
except Exception as e:
    logger.log_exception(
        operation="fetchUserProfile",
        exception=e,
        context={"user_id": "123"},
        ai_todo="Suggest proper error handling for this case"
    )

# Get logs formatted for AI analysis
ai_context = logger.get_logs_for_ai()
```

## 📚 Documentation

For complete documentation, examples, and integration guides, see the main repository [README](../README.md).

## 🔧 Development

### Local Development

```bash
# Clone the repository
git clone https://github.com/vibecoding/vibelogger.git
cd vibelogger/python

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
black vibelogger tests
flake8 vibelogger tests
mypy vibelogger
```

### Project Structure

```
python/
├── vibelogger/           # Main package
│   ├── __init__.py       # Package exports
│   ├── logger.py         # Core VibeCoding Logger
│   ├── config.py         # Configuration management
│   ├── handlers.py       # Standard logging integration
│   └── formatters.py     # Structured logging utilities
├── tests/                # Test suite
├── pyproject.toml        # Package configuration
└── setup.py              # Legacy setup
```

## 🔌 Standard Logging Integration

VibeCoding Logger integrates seamlessly with Python's standard logging:

```python
import logging
from vibelogger import create_file_logger, setup_vibe_logging

# Set up integration
vibe_logger = create_file_logger("my_app")
logger = setup_vibe_logging(vibe_logger, __name__)

# Use standard logging - automatically enhanced!
logger.info("User login", extra={
    'operation': 'user_login',
    'context': {'user_id': '123'},
    'human_note': 'Monitor login patterns'
})
```

## 🎯 Framework Integrations

- **Django** - Complete integration with models, views, middleware
- **FastAPI** - Async-native with dependency injection
- **Flask** - Request context and decorators
- **Standard Logging** - Drop-in replacement with 8 integration patterns

See [examples/integrations/](../examples/integrations/) for detailed implementation guides.

## 🤝 Contributing

Contributions are welcome! Please see the main repository [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

---

Part of the **VibeCoding Logger** multi-language ecosystem.