# VibeCoding Logger 🚀

### AI-Native Logging for LLM Agent Development

**VibeCoding Logger** isn't just another logging tool. It's designed from the ground up for a new era of development where Large Language Models (LLMs) are first-class collaborators. Instead of creating terse, human-readable logs, it produces rich, structured "AI briefing packages" that give LLMs all the context they need to understand, debug, and even modify your code.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.8+-brightgreen.svg)](https://www.python.org/)
[![PyPI version](https://badge.fury.io/py/vibe-logger.svg)](https://badge.fury.io/py/vibe-logger) ---

## The Concept: From Log Lines to Briefing Packages

Traditional logs are made for human eyes. They are concise, but lack the deep context an AI needs. When an LLM agent encounters an error, it needs more than just an error message; it needs to know:
* What was the **goal** (operation)?
* What was the **state** (function arguments, local variables)?
* What was the **environment** (OS, Python version)?
* Are there any **human instructions** or hints?

Vibe Logger bundles all of this into a single, structured JSON entry. Each log is a self-contained briefing that an LLM can use to perform a root cause analysis, suggest a fix, or carry out a task.

---

## Key Features

* 🤖 **LLM-Optimized JSON Format**: Every log is a clean, parsable JSON object.
* 🔗 **Correlation ID Tracking**: Automatically links a series of operations, allowing an AI to trace the entire lifecycle of a request or task.
* 🧠 **Rich Context Injection**: Captures function arguments, environment details, and full stack traces for errors.
* ✍️ **Human-in-the-Loop Fields**: Includes `human_note` and `ai_todo` fields to embed natural language instructions and tasks directly into the logs.
* 🔄 **Automatic Log Rotation**: Prevents log files from growing too large by automatically rotating them based on size.
* 📂 **Effortless File Management**: Automatically creates log directories and timestamped files.
* 🔒 **Thread-Safe**: Designed for use in multi-threaded applications with built-in file and memory locks.
* ⚙️ **Flexible Configuration**: Configure via objects, environment variables, or sensible defaults.

---

## Installation

```bash
pip install vibe-logger
```

Or install directly from your GitHub repository:

```
pip install git/fladdict/vibe-logger.git
```

## How to Use

### Basic Usage
Getting started is simple. Use the create_file_logger helper to create a logger that automatically saves to a timestamped file in ./logs.

```
from vibe_logger import create_file_logger
import time

# 1. Create a logger for your project
# This will create a file like ./logs/my_app-20231027_103000.log
logger = create_file_logger("my_app")

# 2. Log a standard operation with some context
logger.info(
    operation="user_login",
    message="User attempting to log in.",
    context={"username": "alice", "auth_method": "password"}
)

time.sleep(1) # Simulate work

# 3. Log an exception with a note for the AI
try:
    result = 10 / 0
except Exception as e:
    logger.log_exception(
        operation="calculate_ratio",
        exception=e,
        context={"dividend": 10},
        human_note="This calculation is critical. It keeps failing.",
        ai_todo="Analyze the stack trace and suggest a permanent fix that handles division by zero gracefully."
    )

# 4. Get all logs formatted as a JSON string for an AI agent
ai_briefing_package = logger.get_logs_for_ai()
print(ai_briefing_package)
```

### Advanced Usage
For more control, you can create a logger from a configuration object or environment variables.

```
from vibe_logger import create_logger, VibeLoggerConfig

# Configure the logger to use a custom path and larger file size
custom_config = VibeLoggerConfig(
    log_file="./custom_logs/service.log",
    max_file_size_mb=50,
    keep_logs_in_memory=False, # Disable in-memory cache for long-running services
    auto_save=True
)

# Create the logger with the custom configuration
service_logger = create_logger(config=custom_config)

service_logger.warning(
    operation="database_connection",
    message="Connection pool is almost full.",
    context={"pool_size": 100, "active_connections": 95}
)
```





