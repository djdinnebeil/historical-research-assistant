#!/usr/bin/env python3
"""
Utility script to clear Qdrant locks and force close any existing connections.
Use this if you're getting "already accessed" errors.
"""

import os
import sys
from pathlib import Path
import time

def clear_qdrant_locks():
    """Clear any existing Qdrant locks and force cleanup."""
    print("🔧 Clearing Qdrant locks and connections...")
    
    # Import the functions from local_qdrant
    try:
        from local_qdrant import force_close_all_clients, clear_qdrant_cache, force_clear_qdrant_locks
        print("✅ Imported Qdrant functions")
    except ImportError as e:
        print(f"❌ Error importing Qdrant functions: {e}")
        return False
    
    try:
        # Force close all clients
        force_close_all_clients()
        
        # Clear the cache
        clear_qdrant_cache()
        
        # Force clear locks for all projects
        import os
        from pathlib import Path
        
        projects_dir = Path.cwd() / "projects"
        if projects_dir.exists():
            for project_dir in projects_dir.iterdir():
                if project_dir.is_dir():
                    project_name = project_dir.name
                    print(f"🔓 Clearing locks for project: {project_name}")
                    force_clear_qdrant_locks(project_name)
        
        print("✅ Successfully cleared Qdrant locks and connections")
        return True
        
    except Exception as e:
        print(f"❌ Error clearing Qdrant locks: {e}")
        return False

def check_qdrant_processes():
    """Check if there are any Qdrant processes running."""
    print("🔍 Checking for Qdrant processes...")
    
    try:
        import psutil
        
        qdrant_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'qdrant' in proc.info['name'].lower():
                    qdrant_processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if qdrant_processes:
            print(f"⚠️  Found {len(qdrant_processes)} Qdrant processes:")
            for proc in qdrant_processes:
                print(f"   PID {proc['pid']}: {proc['name']}")
            return True
        else:
            print("✅ No Qdrant processes found")
            return False
            
    except ImportError:
        print("⚠️  psutil not available, skipping process check")
        return False

def main():
    """Main function to clear Qdrant locks."""
    print("🚀 Qdrant Lock Cleanup Utility")
    print("=" * 40)
    
    # Check for processes first
    has_processes = check_qdrant_processes()
    
    # Clear locks
    success = clear_qdrant_locks()
    
    if has_processes:
        print("\n⚠️  Note: Qdrant processes were detected.")
        print("   You may need to restart your application or kill these processes manually.")
    
    if success:
        print("\n✅ Cleanup completed successfully!")
        print("   You can now try running your application again.")
    else:
        print("\n❌ Cleanup failed. You may need to:")
        print("   1. Restart your terminal/IDE")
        print("   2. Kill any remaining Qdrant processes")
        print("   3. Restart your application")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
