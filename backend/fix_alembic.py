"""
Manual Migration Fix Script

This script fixes the alembic_version table issue
"""

import psycopg2
from app.core.config import settings

def fix_alembic_version():
    """Fix alembic_version to point to latest migration"""
    
    # Connect to database
    conn = psycopg2.connect(
        "postgresql://postgres:leebpostgre@localhost:5432/scapegis"
    )
    cur = conn.cursor()
    
    try:
        # Check current version
        cur.execute("SELECT * FROM alembic_version;")
        current = cur.fetchone()
        print(f"Current alembic version: {current}")
        
        # Update to the correct latest version (f5404bd9a730)
        cur.execute("UPDATE alembic_version SET version_num = 'f5404bd9a730';")
        conn.commit()
        
        print("✅ Updated alembic_version to f5404bd9a730")
        
        # Verify
        cur.execute("SELECT * FROM alembic_version;")
        new_version = cur.fetchone()
        print(f"New alembic version: {new_version}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    fix_alembic_version()
