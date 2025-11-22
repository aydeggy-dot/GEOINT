"""
Seed Script for Roles and Permissions
Populates the database with default roles and permissions for the Nigeria Security Early Warning System
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.auth import Role, Permission, role_permissions
from datetime import datetime, timezone

# Define all permissions
PERMISSIONS = [
    # Incident permissions
    {"name": "incident.create", "resource": "incident", "action": "create", "description": "Create new security incidents"},
    {"name": "incident.read", "resource": "incident", "action": "read", "description": "View security incidents"},
    {"name": "incident.update", "resource": "incident", "action": "update", "description": "Edit security incidents"},
    {"name": "incident.delete", "resource": "incident", "action": "delete", "description": "Delete security incidents"},
    {"name": "incident.verify", "resource": "incident", "action": "verify", "description": "Verify incident authenticity"},
    {"name": "incident.moderate", "resource": "incident", "action": "moderate", "description": "Moderate incident content"},
    {"name": "incident.publish", "resource": "incident", "action": "publish", "description": "Publish incidents to public"},

    # User permissions
    {"name": "user.read", "resource": "user", "action": "read", "description": "View user profiles"},
    {"name": "user.update", "resource": "user", "action": "update", "description": "Update user information"},
    {"name": "user.delete", "resource": "user", "action": "delete", "description": "Delete user accounts"},
    {"name": "user.manage_roles", "resource": "user", "action": "manage_roles", "description": "Assign and remove user roles"},
    {"name": "user.impersonate", "resource": "user", "action": "impersonate", "description": "Impersonate users for support"},
    {"name": "user.verify", "resource": "user", "action": "verify", "description": "Verify user accounts"},

    # Alert permissions
    {"name": "alert.create", "resource": "alert", "action": "create", "description": "Create security alerts"},
    {"name": "alert.read", "resource": "alert", "action": "read", "description": "View security alerts"},
    {"name": "alert.update", "resource": "alert", "action": "update", "description": "Edit security alerts"},
    {"name": "alert.delete", "resource": "alert", "action": "delete", "description": "Delete security alerts"},
    {"name": "alert.broadcast", "resource": "alert", "action": "broadcast", "description": "Broadcast alerts to public"},

    # Report permissions
    {"name": "report.create", "resource": "report", "action": "create", "description": "Generate reports"},
    {"name": "report.read", "resource": "report", "action": "read", "description": "View reports"},
    {"name": "report.export", "resource": "report", "action": "export", "description": "Export reports"},
    {"name": "report.analyze", "resource": "report", "action": "analyze", "description": "Perform data analysis"},

    # Analytics permissions
    {"name": "analytics.view", "resource": "analytics", "action": "view", "description": "View analytics dashboards"},
    {"name": "analytics.export", "resource": "analytics", "action": "export", "description": "Export analytics data"},
    {"name": "analytics.create_dashboard", "resource": "analytics", "action": "create_dashboard", "description": "Create custom dashboards"},

    # System permissions
    {"name": "system.configure", "resource": "system", "action": "configure", "description": "Configure system settings"},
    {"name": "system.audit", "resource": "system", "action": "audit", "description": "View audit logs"},
    {"name": "system.backup", "resource": "system", "action": "backup", "description": "Manage system backups"},
    {"name": "system.manage_settings", "resource": "system", "action": "manage_settings", "description": "Manage system-wide settings"},
]

# Define roles with their permissions
ROLES = [
    {
        "name": "user",
        "display_name": "User",
        "description": "Basic registered user with limited access",
        "is_system_role": True,
        "permissions": [
            "incident.read",  # Can view public incidents
            "alert.read",     # Can view alerts
        ]
    },
    {
        "name": "verified_reporter",
        "display_name": "Verified Reporter",
        "description": "Verified users who can report security incidents",
        "is_system_role": True,
        "permissions": [
            "incident.create",  # Can report incidents
            "incident.read",    # Can view incidents
            "incident.update",  # Can edit their own reports
            "alert.read",       # Can view alerts
            "report.read",      # Can view reports
        ]
    },
    {
        "name": "moderator",
        "display_name": "Moderator",
        "description": "Content moderators who verify and manage incidents",
        "is_system_role": True,
        "permissions": [
            "incident.create",
            "incident.read",
            "incident.update",
            "incident.verify",     # Can verify incidents
            "incident.moderate",   # Can moderate content
            "incident.publish",    # Can publish incidents
            "alert.read",
            "alert.create",        # Can create alerts
            "alert.update",
            "user.read",           # Can view user profiles
            "report.read",
            "analytics.view",
        ]
    },
    {
        "name": "analyst",
        "display_name": "Security Analyst",
        "description": "Analysts who can analyze data and generate reports",
        "is_system_role": True,
        "permissions": [
            "incident.create",
            "incident.read",
            "incident.update",
            "incident.verify",
            "alert.read",
            "alert.create",
            "alert.update",
            "report.create",       # Can generate reports
            "report.read",
            "report.export",       # Can export data
            "report.analyze",      # Can perform analysis
            "analytics.view",      # Can view analytics
            "analytics.export",    # Can export analytics
            "analytics.create_dashboard",  # Can create dashboards
            "user.read",
        ]
    },
    {
        "name": "admin",
        "display_name": "Administrator",
        "description": "System administrators with full management capabilities",
        "is_system_role": True,
        "permissions": [
            # All incident permissions
            "incident.create",
            "incident.read",
            "incident.update",
            "incident.delete",
            "incident.verify",
            "incident.moderate",
            "incident.publish",
            # All alert permissions
            "alert.create",
            "alert.read",
            "alert.update",
            "alert.delete",
            "alert.broadcast",
            # All user permissions except impersonate
            "user.read",
            "user.update",
            "user.delete",
            "user.manage_roles",
            "user.verify",
            # All report permissions
            "report.create",
            "report.read",
            "report.export",
            "report.analyze",
            # All analytics permissions
            "analytics.view",
            "analytics.export",
            "analytics.create_dashboard",
            # Most system permissions
            "system.configure",
            "system.audit",
            "system.manage_settings",
        ]
    },
    {
        "name": "super_admin",
        "display_name": "Super Administrator",
        "description": "Ultimate system control with all permissions",
        "is_system_role": True,
        "permissions": [
            # All permissions (list all permission names)
            perm["name"] for perm in PERMISSIONS
        ]
    }
]


def seed_permissions(db: Session):
    """Create all permissions in the database"""
    print("\n" + "="*60)
    print("SEEDING PERMISSIONS")
    print("="*60)

    created_count = 0
    existing_count = 0

    for perm_data in PERMISSIONS:
        # Check if permission already exists
        existing = db.query(Permission).filter_by(name=perm_data["name"]).first()

        if existing:
            print(f"  [EXISTS] {perm_data['name']}")
            existing_count += 1
        else:
            permission = Permission(**perm_data)
            db.add(permission)
            print(f"  [CREATE] {perm_data['name']} - {perm_data['description']}")
            created_count += 1

    db.commit()

    print(f"\n  Summary: {created_count} created, {existing_count} already existed")
    print(f"  Total permissions in database: {db.query(Permission).count()}")
    return created_count, existing_count


def seed_roles(db: Session):
    """Create all roles and assign permissions"""
    print("\n" + "="*60)
    print("SEEDING ROLES")
    print("="*60)

    created_count = 0
    existing_count = 0

    for role_data in ROLES:
        # Extract permission names
        permission_names = role_data.pop("permissions")

        # Check if role already exists
        existing_role = db.query(Role).filter_by(name=role_data["name"]).first()

        if existing_role:
            print(f"\n  [EXISTS] {role_data['name']} - {role_data['display_name']}")
            role = existing_role
            existing_count += 1
        else:
            role = Role(**role_data)
            db.add(role)
            db.flush()  # Get the role ID
            print(f"\n  [CREATE] {role_data['name']} - {role_data['display_name']}")
            print(f"           {role_data['description']}")
            created_count += 1

        # Assign permissions to role
        permissions = db.query(Permission).filter(Permission.name.in_(permission_names)).all()
        role.permissions = permissions

        print(f"  [PERMS]  Assigned {len(permissions)} permissions:")
        for perm in permissions:
            print(f"           - {perm.name}")

    db.commit()

    print(f"\n  Summary: {created_count} created, {existing_count} already existed")
    print(f"  Total roles in database: {db.query(Role).count()}")
    return created_count, existing_count


def main():
    """Main seeding function"""
    print("\n" + "="*60)
    print("ROLE & PERMISSION SEEDING SCRIPT")
    print("Nigeria Security Early Warning System")
    print("="*60)

    db = SessionLocal()

    try:
        # Seed permissions first
        perm_created, perm_existing = seed_permissions(db)

        # Then seed roles with their permissions
        role_created, role_existing = seed_roles(db)

        # Final summary
        print("\n" + "="*60)
        print("SEEDING COMPLETE!")
        print("="*60)
        print(f"\nPermissions:")
        print(f"  - Created: {perm_created}")
        print(f"  - Already existed: {perm_existing}")
        print(f"  - Total: {db.query(Permission).count()}")

        print(f"\nRoles:")
        print(f"  - Created: {role_created}")
        print(f"  - Already existed: {role_existing}")
        print(f"  - Total: {db.query(Role).count()}")

        print("\n" + "="*60)
        print("ROLE BREAKDOWN:")
        print("="*60)

        for role in db.query(Role).order_by(Role.name).all():
            perm_count = len(role.permissions)
            print(f"\n  [{role.name}] - {role.display_name}")
            print(f"  Permissions: {perm_count}")
            print(f"  System Role: {'Yes' if role.is_system_role else 'No'}")

        print("\n" + "="*60)
        print("SUCCESS! Database seeded successfully.")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n[ERROR] Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
