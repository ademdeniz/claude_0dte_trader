#!/usr/bin/env python3
"""
Database Migration: AI Features

Safely applies schema changes for AI dashboard features.
Backs up existing database before applying changes.
"""

import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

# Database paths
DB_PATH = Path("trades.db")
BACKUP_PATH = Path(f"trades_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
MIGRATION_FILE = Path("schema_migration_ai_features.sql")

def backup_database():
    """Create backup of existing database"""
    if DB_PATH.exists():
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"✅ Database backed up to: {BACKUP_PATH}")
        return True
    else:
        print("⚠️  No existing database found - creating fresh database")
        return False

def apply_migration():
    """Apply the AI features schema migration"""
    try:
        # Read migration SQL
        with open(MIGRATION_FILE, 'r') as f:
            migration_sql = f.read()

        # Apply migration
        with sqlite3.connect(DB_PATH) as conn:
            conn.executescript(migration_sql)
            print("✅ Schema migration applied successfully")

        return True

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

def verify_migration():
    """Verify migration was applied correctly"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()

            # Check that all new tables exist
            expected_tables = [
                'ai_briefings',
                'ai_analyses',
                'ai_gut_checks',
                'ai_reviews',
                'user_education'
            ]

            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]

            missing_tables = [t for t in expected_tables if t not in existing_tables]

            if missing_tables:
                print(f"❌ Migration verification failed. Missing tables: {missing_tables}")
                return False
            else:
                print("✅ Migration verification passed - all tables created")

            # Check view exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='ai_usage_summary'")
            if cursor.fetchone():
                print("✅ AI usage summary view created")
            else:
                print("⚠️  AI usage summary view not found")

            return True

    except Exception as e:
        print(f"❌ Migration verification failed: {e}")
        return False

def rollback_migration():
    """Rollback migration using backup"""
    if BACKUP_PATH.exists():
        try:
            shutil.copy2(BACKUP_PATH, DB_PATH)
            print(f"✅ Database rolled back from backup: {BACKUP_PATH}")
            return True
        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False
    else:
        print("❌ No backup found for rollback")
        return False

def main():
    """Run migration process"""
    print("🚀 Starting AI Features Database Migration")
    print("=" * 50)

    # Step 1: Backup existing database
    print("\n📁 Step 1: Creating backup...")
    backup_created = backup_database()

    # Step 2: Apply migration
    print("\n🔧 Step 2: Applying schema changes...")
    migration_success = apply_migration()

    if not migration_success:
        if backup_created:
            print("\n🔄 Rolling back changes...")
            rollback_migration()
        return False

    # Step 3: Verify migration
    print("\n✅ Step 3: Verifying migration...")
    verification_success = verify_migration()

    if not verification_success:
        if backup_created:
            print("\n🔄 Rolling back changes...")
            rollback_migration()
        return False

    print("\n🎉 Migration completed successfully!")
    print(f"   Backup saved as: {BACKUP_PATH}")
    print("   AI features database schema is ready")

    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Migration failed - please check errors above")
        exit(1)
    else:
        print("\n✅ Ready to proceed with AI dashboard features!")
        exit(0)