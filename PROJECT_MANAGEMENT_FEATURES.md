# Project Management Features

This document describes the new project management capabilities added to the Historical Research Assistant.

## Overview

The application now includes comprehensive project management functionality that allows users to:
- Archive projects for backup purposes
- Delete projects with confirmation dialogs
- Restore archived projects
- View project statistics and information

## New Navigation Option

A new "Project Management" option has been added to the sidebar navigation menu, positioned after "Document Manager" and before "Ask Questions".

## Features

### 1. Project Information Display

The Project Management interface shows:
- Project name and collection name
- Document count
- Vector store status (Active/Not Found)
- Project size in MB

### 2. Project Archiving

**Archive Project Button**: Moves the project to a timestamped archive in the `archive/` directory.

- Archive naming format: `{project_name}_{YYYYMMDD_HHMMSS}`
- Projects are moved (not copied) to the `archive/` directory
- After successful archiving, the project is removed from active projects
- User is redirected to project selection

### 3. Project Deletion

**Delete Project Button**: Provides multiple deletion options with safety confirmations.

When the delete button is clicked, users are presented with three options:

1. **Cancel** (❌): Aborts the deletion process
2. **Archive Project** (📦): Moves the project to archive (recommended)
3. **Delete Only** (🗑️): Deletes the project without archiving

**Safety Features:**
- Clear warning messages about permanent deletion
- Option to archive instead of deletion
- Confirmation dialogs prevent accidental deletions
- Automatic cleanup of Qdrant cache and session state

### 4. Project Restoration

**Restore Button**: Allows users to restore archived projects.

- Restores projects from the archive directory
- Checks for naming conflicts before restoration
- Removes the archive after successful restoration
- Automatically switches to the restored project

### 5. Archive Management

The interface displays all archived projects with:
- Project name and archive timestamp
- Archive size in MB
- Individual restore buttons for each archive

## Technical Implementation

### File Structure

```
historical_research_assistant/
├── components/
│   └── project_manager.py      # New component
├── archive/                     # Archive directory
│   └── .gitkeep               # Ensures directory is tracked by git
├── projects/                   # Active projects
└── app.py                     # Updated with new navigation
```

### Key Functions

- `ensure_archive_dir()`: Creates archive directory if it doesn't exist
- `archive_project()`: Copies project to archive with timestamp
- `delete_project()`: Removes project with cleanup
- `restore_project()`: Restores project from archive
- `render_project_manager()`: Main UI rendering function

### Safety Measures

1. **Session State Management**: Automatically resets session state when projects are deleted
2. **Qdrant Cache Clearing**: Prevents stale connections after project deletion
3. **Existence Checks**: Verifies project existence before operations
4. **Error Handling**: Comprehensive error handling with user-friendly messages
5. **Confirmation Dialogs**: Multiple confirmation steps for destructive operations

## Usage Examples

### Archiving a Project

1. Navigate to "Project Management" in the sidebar
2. Click "📦 Archive Project"
3. Project is moved to archive with timestamp
4. Project is removed from active projects
5. User is redirected to project selection

### Deleting a Project

1. Navigate to "Project Management" in the sidebar
2. Click "🗑️ Delete Project"
3. Choose deletion option:
   - Archive Project (recommended)
   - Delete Only
   - Cancel
4. Confirm the action

### Restoring an Archived Project

1. Navigate to "Project Management" in the sidebar
2. Scroll to "Archive Information" section
3. Click "🔄 Restore" button next to desired archive
4. Project is restored and archive is removed

## Error Handling

The system handles various error scenarios:
- Project already exists during restoration
- File system permission issues
- Insufficient disk space
- Corrupted project files
- Network issues (if applicable)

All errors are displayed to the user with clear messages and suggestions.

## Best Practices

1. **Always archive before deletion** to preserve data
2. **Regular archiving** of important projects
3. **Monitor archive directory size** to prevent disk space issues
4. **Test restoration** periodically to ensure archives are valid
5. **Use descriptive project names** for easier archive management

## Future Enhancements

Potential improvements for future versions:
- Archive compression to save disk space
- Archive expiration and automatic cleanup
- Archive search and filtering
- Archive metadata and tagging
- Bulk archive operations
- Archive integrity verification
- Cloud storage integration for archives
