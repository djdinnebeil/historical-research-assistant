# Logging Control Examples

This file shows how easy it is to control logging in your Historical Research Assistant.

## 🎯 Simple Configuration

Just open `config.py` and change these two lines:

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

## 📋 Common Settings

### 1. **Normal Operation** (Default)
```python
DISABLE_LOGGING = False
LOG_LEVEL = "INFO"
```
*Shows important information and warnings*

### 2. **Debug Mode** (Troubleshooting)
```python
DISABLE_LOGGING = False
LOG_LEVEL = "DEBUG"
```
*Shows everything - very verbose*

### 3. **Quiet Mode** (Warnings Only)
```python
DISABLE_LOGGING = False
LOG_LEVEL = "WARNING"
```
*Shows only warnings and errors*

### 4. **Silent Mode** (No Logging)
```python
DISABLE_LOGGING = True
LOG_LEVEL = "INFO"  # This doesn't matter when disabled
```
*Completely silent - no log output*

### 5. **Error Only Mode**
```python
DISABLE_LOGGING = False
LOG_LEVEL = "ERROR"
```
*Shows only errors*

## 🚀 How to Use

1. **Open** `config.py` in your editor
2. **Find** the "EASY LOGGING CONTROL" section
3. **Change** the values as needed
4. **Save** the file
5. **Restart** your application

That's it! No environment variables, no command line flags - just simple Python variables.

## 🔄 Quick Changes

**To disable logging temporarily:**
```python
DISABLE_LOGGING = True
```

**To enable debug mode:**
```python
LOG_LEVEL = "DEBUG"
```

**To go back to normal:**
```python
DISABLE_LOGGING = False
LOG_LEVEL = "INFO"
```

## 📊 Log Levels Explained

- **DEBUG**: Everything (very verbose)
- **INFO**: General information (default)
- **WARNING**: Something unexpected happened
- **ERROR**: A serious error occurred
- **CRITICAL**: Only critical errors

The higher the level, the less verbose the output.
