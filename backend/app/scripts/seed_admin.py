"""Seed admin account"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.session import SessionLocal
from app.services.admin_seed_service import seed_admin

def main():
    print("Seeding admin account...")
    db = SessionLocal()
    try:
        admin = seed_admin(db)
        print(f"\nAdmin Details:")
        print(f"  Email: {admin.email}")
        print(f"  Name: {admin.name}")
        print(f"  Role: {admin.role}")
        print(f"  ID: {admin.id}")
        print(f"\n✅ Seeding completed successfully!")
    except Exception as e:
        print(f"❌ Error seeding admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
