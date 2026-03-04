#!/usr/bin/env python3
"""
Automatic fix script for Activity Timeline ordering issue.

This script:
1. Finds the /activity endpoint in backend/app.py
2. Changes ORDER BY id DESC to ORDER BY timestamp DESC, id DESC
3. Adds database index for performance
4. Creates backup before making changes

Usage:
    python fix_activity_timeline.py
"""

import re
import shutil
import sqlite3
from pathlib import Path
from datetime import datetime


class ActivityTimelineFix:
    def __init__(self):
        self.backend_dir = Path(__file__).parent / "backend"
        self.app_py = self.backend_dir / "app.py"
        self.db_path = self.backend_dir / "engageflow.db"
        self.backup_dir = Path(__file__).parent / "backups"
        
    def create_backup(self):
        """Create timestamped backup of app.py"""
        self.backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"app_py_backup_{timestamp}.py"
        shutil.copy2(self.app_py, backup_path)
        print(f"✓ Created backup: {backup_path}")
        return backup_path
    
    def fix_backend_ordering(self):
        """Fix the SQL query in /activity endpoint"""
        if not self.app_py.exists():
            print(f"✗ Error: {self.app_py} not found")
            return False
        
        content = self.app_py.read_text(encoding="utf-8")
        
        # Pattern 1: Direct ORDER BY id DESC
        pattern1 = r'(SELECT\s+\*\s+FROM\s+logs\s+ORDER\s+BY\s+)id(\s+DESC\s+LIMIT)'
        replacement1 = r'\1timestamp DESC, id\2'
        
        # Pattern 2: With parentheses/formatting
        pattern2 = r'(ORDER\s+BY\s+)id(\s+DESC)(?=\s*\n?\s*LIMIT)'
        replacement2 = r'\1timestamp DESC, id\2'
        
        modified = content
        count = 0
        
        # Try pattern 1
        modified, n1 = re.subn(pattern1, replacement1, modified, flags=re.IGNORECASE)
        count += n1
        
        # Try pattern 2 if pattern 1 didn't match
        if n1 == 0:
            modified, n2 = re.subn(pattern2, replacement2, modified, flags=re.IGNORECASE)
            count += n2
        
        if count == 0:
            print("⚠ Warning: Could not find exact pattern. Searching for manual fix location...")
            # Find lines with logs table queries
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if 'logs' in line.lower() and 'order by' in line.lower() and 'id' in line.lower():
                    print(f"\n   Found at line {i}: {line.strip()[:80]}...")
            print("\n   Please manually change 'ORDER BY id DESC' to 'ORDER BY timestamp DESC, id DESC'")
            return False
        
        self.app_py.write_text(modified, encoding="utf-8")
        print(f"✓ Fixed {count} occurrence(s) in {self.app_py}")
        print("  Changed: ORDER BY id DESC → ORDER BY timestamp DESC, id DESC")
        return True
    
    def add_database_index(self):
        """Add performance index to logs table"""
        if not self.db_path.exists():
            print(f"⚠ Warning: {self.db_path} not found, skipping index creation")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if index already exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_logs_timestamp_desc'"
            )
            if cursor.fetchone():
                print("✓ Database index already exists")
                conn.close()
                return True
            
            # Create index
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_logs_timestamp_desc ON logs(timestamp DESC, id DESC)"
            )
            conn.commit()
            conn.close()
            
            print("✓ Created database index: idx_logs_timestamp_desc")
            return True
            
        except sqlite3.Error as e:
            print(f"✗ Database error: {e}")
            return False
    
    def verify_fix(self):
        """Verify the fix was applied correctly"""
        content = self.app_py.read_text(encoding="utf-8")
        
        # Check for correct pattern
        if re.search(r'ORDER\s+BY\s+timestamp\s+DESC,\s*id\s+DESC', content, re.IGNORECASE):
            print("✓ Verification passed: ORDER BY timestamp DESC, id DESC found")
            return True
        else:
            print("✗ Verification failed: Could not find corrected ORDER BY clause")
            return False
    
    def run(self):
        """Execute the complete fix"""
        print("="*60)
        print("Activity Timeline Fix - Once and For All")
        print("="*60)
        print()
        
        # Step 1: Backup
        print("[1/4] Creating backup...")
        self.create_backup()
        print()
        
        # Step 2: Fix backend
        print("[2/4] Fixing backend ordering...")
        if not self.fix_backend_ordering():
            print("\n✗ Fix aborted. Please apply manual fix.")
            return False
        print()
        
        # Step 3: Database index
        print("[3/4] Adding database index...")
        self.add_database_index()
        print()
        
        # Step 4: Verify
        print("[4/4] Verifying fix...")
        if not self.verify_fix():
            print("\n⚠ Fix may not be complete. Please verify manually.")
            return False
        print()
        
        print("="*60)
        print("✓ FIX COMPLETE!")
        print("="*60)
        print()
        print("Next steps:")
        print("1. Restart backend: cd backend && python -m uvicorn app:app --reload")
        print("2. Refresh frontend in browser")
        print("3. Test: Add comment in Inbox at current time (e.g., 02:52 PM)")
        print("4. Verify it appears at TOP of Activity Timeline")
        print()
        return True


if __name__ == "__main__":
    fixer = ActivityTimelineFix()
    success = fixer.run()
    exit(0 if success else 1)
