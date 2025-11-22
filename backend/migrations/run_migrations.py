#!/usr/bin/env python3
"""
Database Migration Script
=========================
Run this script to add missing columns and tables to your database.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from models.database import engine, AsyncSessionLocal


async def run_migrations():
    """Run database migrations."""
    if not engine:
        print("❌ DATABASE_URL not set. Cannot run migrations.")
        sys.exit(1)
    
    print("🔄 Running database migrations...")
    
    async with engine.begin() as conn:
        # Migration 1: Add is_admin column
        print("  → Adding is_admin column to users table...")
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT false;
            """))
            print("  ✅ Added is_admin column")
        except Exception as e:
            print(f"  ⚠️  Error adding is_admin column: {e}")
        
        # Create index for is_admin
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_is_admin ON users(is_admin);
            """))
            print("  ✅ Created index on is_admin")
        except Exception as e:
            print(f"  ⚠️  Error creating index: {e}")
        
        # Migration 2: Create audit_logs table
        print("  → Creating audit_logs table...")
        try:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id SERIAL PRIMARY KEY,
                    admin_user_id VARCHAR(255) NOT NULL,
                    admin_email VARCHAR(255) NOT NULL,
                    action VARCHAR(100) NOT NULL,
                    resource_type VARCHAR(50),
                    resource_id VARCHAR(255),
                    details TEXT,
                    ip_address VARCHAR(50),
                    user_agent TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """))
            print("  ✅ Created audit_logs table")
        except Exception as e:
            print(f"  ⚠️  Error creating audit_logs table: {e}")
        
        # Create indexes for audit_logs
        try:
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_audit_logs_admin_user_id ON audit_logs(admin_user_id);
                CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
                CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
            """))
            print("  ✅ Created indexes on audit_logs")
        except Exception as e:
            print(f"  ⚠️  Error creating indexes: {e}")
    
    print("\n✅ Migrations completed successfully!")
    print("\n💡 Next steps:")
    print("   1. Set ADMIN_EMAILS environment variable with your email")
    print("   2. Log in via Google OAuth")
    print("   3. You'll automatically get admin access")


if __name__ == "__main__":
    asyncio.run(run_migrations())

