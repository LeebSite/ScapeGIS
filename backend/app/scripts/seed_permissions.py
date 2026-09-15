import sys
import os

# Add parent directory to path to allow running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.db.session import SessionLocal
from app.db.models.permission import Permission, RolePermission
from app.db.models.user import UserRole

def seed_permissions():
    db = SessionLocal()
    
    permissions_data = [
        # User management
        {"name": "users.read", "description": "View users", "category": "users"},
        {"name": "users.create", "description": "Create users", "category": "users"},
        {"name": "users.update", "description": "Update users", "category": "users"},
        {"name": "users.delete", "description": "Delete users", "category": "users"},
        {"name": "users.update_role", "description": "Change user roles", "category": "users"},
        {"name": "users.update_status", "description": "Change user active status", "category": "users"},
        
        # Audit logs
        {"name": "audit.read", "description": "View audit logs", "category": "audit"},
    ]
    
    print("Creating/Updating permissions...")
    # Create permissions
    created_permissions = {}
    for perm_data in permissions_data:
        existing = db.query(Permission).filter(Permission.name == perm_data['name']).first()
        if not existing:
            perm = Permission(**perm_data)
            db.add(perm)
            db.commit()
            db.refresh(perm)
            created_permissions[perm.name] = perm.id
            print(f"  + Created permission: {perm.name}")
        else:
            created_permissions[perm_data['name']] = existing.id
            print(f"  . Perimssion exists: {existing.name}")
    
    # Assign permissions to roles
    role_permissions_map = {
        UserRole.ADMIN: [
            "users.read", "users.create", "users.update", "users.delete", 
            "users.update_role", "users.update_status", "audit.read"
        ],
        UserRole.DEVELOPER: [
            # Minimal access for developer role for now
            # "users.read" # Maybe developer can read users? Let's say no for now.
        ],
    }
    
    print("\nAssigning permissions to roles...")
    for role, permission_names in role_permissions_map.items():
        for perm_name in permission_names:
            perm_id = created_permissions.get(perm_name)
            if not perm_id:
                print(f"  ! Warning: Permission {perm_name} not found")
                continue
                
            existing = db.query(RolePermission).filter(
                RolePermission.role == role,
                RolePermission.permission_id == perm_id
            ).first()
            
            if not existing:
                role_perm = RolePermission(
                    role=role,
                    permission_id=perm_id
                )
                db.add(role_perm)
                print(f"  + Assigned {perm_name} to {role}")
            else:
                print(f"  . {perm_name} already assigned to {role}")
    
    db.commit()
    print("✅ Permissions seeded successfully")
    db.close()

if __name__ == "__main__":
    seed_permissions()
