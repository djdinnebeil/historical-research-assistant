#!/usr/bin/env python3
"""
Test script to verify database updates are working correctly.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def test_database_updates():
    """Test that database updates work correctly."""
    
    try:
        from db import ensure_db, set_project_db, list_documents_by_status, update_document_status
        
        # Test with a test project
        project_name = "test_db_project"
        set_project_db(project_name)
        con = ensure_db()
        
        print(f"✅ Database connection established for project: {project_name}")
        
        # Check initial state
        initial_pending = list_documents_by_status(con, "pending")
        initial_embedded = list_documents_by_status(con, "embedded")
        
        print(f"Initial pending documents: {len(initial_pending)}")
        print(f"Initial embedded documents: {len(initial_embedded)}")
        
        # If there are pending documents, try to update one
        if initial_pending:
            test_row = initial_pending[0]
            content_hash = test_row[7]  # content_hash is at index 7
            path = test_row[1]  # path is at index 1
            
            print(f"Testing update on document: {path}")
            print(f"Content hash: {content_hash}")
            
            # Try to update the status
            update_document_status(con, content_hash, 5, "embedded")
            print("✅ update_document_status() called successfully")
            
            # Check if the update worked
            updated_pending = list_documents_by_status(con, "pending")
            updated_embedded = list_documents_by_status(con, "embedded")
            
            print(f"After update - pending: {len(updated_pending)}, embedded: {len(updated_embedded)}")
            
            # Verify the specific document was updated
            all_docs = con.execute("SELECT * FROM documents WHERE content_hash = ?", (content_hash,)).fetchall()
            if all_docs:
                doc = all_docs[0]
                status = doc[8]  # status is at index 8
                num_chunks = doc[6]  # num_chunks is at index 6
                print(f"Document status: {status}, num_chunks: {num_chunks}")
                
                if status == "embedded" and num_chunks == 5:
                    print("✅ Database update verified successfully!")
                else:
                    print(f"❌ Database update failed - expected status='embedded', num_chunks=5, got status='{status}', num_chunks={num_chunks}")
            else:
                print("❌ Could not find document after update")
                
        else:
            print("ℹ️ No pending documents to test with")
            
        # Clean up test project
        con.close()
        test_db_path = Path("projects") / project_name / f"{project_name}.sqlite"
        if test_db_path.exists():
            test_db_path.unlink()
            print("✅ Test database cleaned up")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_updates()
