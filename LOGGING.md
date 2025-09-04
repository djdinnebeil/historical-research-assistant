# Logging Configuration

This project now uses Python's built-in `logging` module for better debugging and monitoring.

## Configuration

Logging is configured in `config.py` with simple, easy-to-modify settings:

### **Easy Control (Recommended)**

Open `config.py` and modify these simple settings:

```python
# =============================================================================
# EASY LOGGING CONTROL - MODIFY THESE SETTINGS AS NEEDED
# =============================================================================

# Set to True to disable all logging output
DISABLE_LOGGING = False

# Set the logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
# DEBUG = most verbose, CRITICAL = least verbose
LOG_LEVEL = "INFO"
```

### **Features**

- **Simple Flags**: Just change `True`/`False` and log level strings
- **Output**: All logs are sent to the terminal/console
- **Format**: Timestamp, logger name, level, and message
- **Third-party Libraries**: Reduced verbosity for external libraries (Streamlit, OpenAI, etc.)

## Usage

### Basic Usage

```python
from config import get_logger

logger = get_logger(__name__)

# Log messages at different levels
logger.debug("Detailed debugging information")
logger.info("General information about program execution")
logger.warning("Something unexpected happened")
logger.error("A serious error occurred")
```

### Log Levels

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General information about program execution
- **WARNING**: Something unexpected happened, but the program is still working
- **ERROR**: A serious error occurred

### Quick Examples

**To disable logging completely:**
```python
# In config.py
DISABLE_LOGGING = True
```

**To show only errors and warnings:**
```python
# In config.py
LOG_LEVEL = "WARNING"
```

**To show everything (debug mode):**
```python
# In config.py
LOG_LEVEL = "DEBUG"
```

**To show only critical errors:**
```python
# In config.py
LOG_LEVEL = "CRITICAL"
```

### Environment Variables (Advanced)

You can still override these settings with environment variables:

```bash
# Override with environment variables
LOG_LEVEL=DEBUG streamlit run app.py
DISABLE_LOGGING=true streamlit run app.py
```

## What Was Changed

1. **Added logging configuration** to `config.py`
2. **Replaced print statements** with proper logging calls throughout the codebase
3. **Added logger initialization** to main application entry points
4. **Configured third-party library verbosity** to reduce noise

## Benefits

- **Better debugging**: Structured log messages with timestamps and levels
- **Configurable verbosity**: Control how much information is shown
- **Professional logging**: Industry-standard logging practices
- **Performance**: No performance impact when logging is disabled
- **Filtering**: Easy to filter logs by level or module

## Example Output

```
2025-09-03 15:45:53 - config - INFO - Logging configured with level: INFO
2025-09-03 15:45:53 - app - INFO - Starting Historical Research Assistant
2025-09-03 15:45:53 - components.state_manager - INFO - Project change detected: old_project → new_project
2025-09-03 15:45:53 - core.vector_store - INFO - Indexing 5 files from /path/to/documents …
2025-09-03 15:45:53 - core.vector_store - DEBUG - Staged 12 chunks from document1.txt
```
