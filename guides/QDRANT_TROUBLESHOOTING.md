# Qdrant "Already Accessed" Error Troubleshooting

## Problem
You're getting this error when running your Streamlit app:
```
RuntimeError: Storage folder /path/to/projects/amatol/qdrant is already accessed by another instance of Qdrant client. If you require concurrent access, use Qdrant server instead.
```

## Root Cause
This error occurs when multiple Qdrant client instances try to access the same local storage path simultaneously. This commonly happens in Streamlit apps due to:

1. **Streamlit caching conflicts** - The `@st.cache_resource` decorator may not be working as expected
2. **Multiple processes** - Streamlit may be running multiple instances
3. **Stale connections** - Previous connections weren't properly closed
4. **File locks** - SQLite database files are locked by another process

## Solutions Implemented

### 1. Enhanced Error Handling
The `get_qdrant_client()` function now includes better error handling:
- Catches "already accessed" errors
- Automatically clears the cache and retries
- Includes a small delay to allow cleanup

### 2. Client Registry System
Added a client tracking system to monitor active connections:
- `_active_clients` dictionary tracks all active clients
- `is_client_active()` checks if a client is already running
- `force_close_all_clients()` closes all clients forcefully
- `close_qdrant_client()` closes a specific project's client

### 3. Improved Cache Management
Enhanced the `clear_qdrant_cache()` function:
- Clears Streamlit's cached clients
- Closes all active client connections
- Resets the client registry

### 4. Better Project Switching
The sidebar now properly closes previous clients when switching projects:
- Calls `close_qdrant_client()` before switching
- Clears the cache to force fresh connections
- Provides user feedback about the switch

### 5. App Initialization Cleanup
Added cleanup on app startup:
- Clears any stale connections when the app starts
- Prevents conflicts from previous sessions

## How to Use

### Immediate Fix
If you're currently experiencing the error:

1. **Stop your Streamlit app** (Ctrl+C)
2. **Run the cleanup utility:**
   ```bash
   python clear_qdrant_locks.py
   ```
3. **Restart your Streamlit app:**
   ```bash
   streamlit run app.py
   ```

### Manual Cleanup
If the utility doesn't work:

1. **Close all terminals/IDEs** that might be running the app
2. **Check for Qdrant processes:**
   ```bash
   ps aux | grep qdrant
   ```
3. **Kill any found processes:**
   ```bash
   kill -9 <PID>
   ```
4. **Restart your application**

### Prevention
To prevent this issue in the future:

1. **Always use the sidebar project switcher** instead of manually changing projects
2. **Let the app handle client lifecycle** - don't manually create Qdrant clients
3. **Restart the app** if you encounter any Qdrant-related errors

## Alternative Solutions

### Use Qdrant Server (Recommended for Production)
Instead of local storage, use a Qdrant server:
```python
# In local_qdrant.py, change:
client = QdrantClient(path=str(qdrant_path))

# To:
client = QdrantClient(url="http://localhost:6333")
```

### Disable Caching (Not Recommended)
You can disable caching, but this will impact performance:
```python
# Remove the @st.cache_resource decorator
def get_qdrant_client(project_name: str) -> QdrantClient:
    # ... function body
```

## Code Changes Made

### local_qdrant.py
- Added client registry system
- Enhanced error handling in `get_qdrant_client()`
- Added utility functions for client management
- Improved cache clearing

### components/sidebar.py
- Added proper client cleanup when switching projects
- Better error handling and user feedback

### app.py
- Added initialization cleanup
- Prevents stale connections on startup

## Testing
After implementing these fixes:

1. **Test project switching** - Switch between different projects multiple times
2. **Test app restart** - Stop and restart the app several times
3. **Monitor for errors** - Check the console for any remaining issues

## Still Having Issues?
If the problem persists:

1. **Check file permissions** - Ensure the projects directory is writable
2. **Verify no other apps** are using the same Qdrant storage
3. **Consider using Qdrant server** instead of local storage
4. **Check Streamlit version** - Ensure you're using a recent version

## Support
If you continue to experience issues, please:
1. Check the console output for specific error messages
2. Verify your project structure and file permissions
3. Consider sharing the complete error traceback
