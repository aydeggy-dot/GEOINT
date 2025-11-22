# RBAC System Documentation

**Nigeria Security Early Warning System**
**Date**: November 21, 2025
**Version**: 1.0

---

## Overview

The Nigeria Security Early Warning System implements a comprehensive Role-Based Access Control (RBAC) system with 6 predefined roles and 29 granular permissions across 6 resource types.

**Key Features:**
- Hierarchical role structure from basic users to super administrators
- Granular permissions for fine-grained access control
- System roles protected from deletion
- Many-to-many relationships (users can have multiple roles)
- Database-enforced constraints for data integrity

---

## Roles

### 1. User (user)
**Description**: Basic registered user with limited access
**Permission Count**: 2
**Use Case**: General public users who want to view security information

**Permissions:**
- `incident.read` - View public security incidents
- `alert.read` - View security alerts

---

### 2. Verified Reporter (verified_reporter)
**Description**: Verified users who can report security incidents
**Permission Count**: 5
**Use Case**: Trusted community members who report incidents

**Permissions:**
- `incident.create` - Report new security incidents
- `incident.read` - View security incidents
- `incident.update` - Edit their own incident reports
- `alert.read` - View security alerts
- `report.read` - View generated reports

**Verification Requirements:**
- Email verification required
- Additional identity verification may be required
- Trust score monitoring

---

### 3. Moderator (moderator)
**Description**: Content moderators who verify and manage incidents
**Permission Count**: 12
**Use Case**: Staff members who verify incident authenticity and moderate content

**Permissions:**
- `incident.create` - Create incidents
- `incident.read` - View all incidents
- `incident.update` - Edit any incident
- `incident.verify` - Mark incidents as verified
- `incident.moderate` - Moderate incident content
- `incident.publish` - Publish incidents to public view
- `user.read` - View user profiles
- `alert.create` - Create security alerts
- `alert.read` - View alerts
- `alert.update` - Edit alerts
- `report.read` - View reports
- `analytics.view` - View analytics dashboards

---

### 4. Security Analyst (analyst)
**Description**: Analysts who can analyze data and generate reports
**Permission Count**: 15
**Use Case**: Security analysts who study trends and generate intelligence reports

**Permissions:**
- `incident.create` - Create incidents
- `incident.read` - View all incidents
- `incident.update` - Edit incidents
- `incident.verify` - Verify incidents
- `user.read` - View user information
- `alert.create` - Create alerts
- `alert.read` - View alerts
- `alert.update` - Edit alerts
- `report.create` - Generate reports
- `report.read` - View reports
- `report.export` - Export report data
- `report.analyze` - Perform data analysis
- `analytics.view` - View analytics dashboards
- `analytics.export` - Export analytics data
- `analytics.create_dashboard` - Create custom dashboards

---

### 5. Administrator (admin)
**Description**: System administrators with full management capabilities
**Permission Count**: 27 (all except `user.impersonate` and `system.backup`)
**Use Case**: System administrators who manage the platform

**Permissions:**

**Incident Management (7):**
- `incident.create` - Create incidents
- `incident.read` - View all incidents
- `incident.update` - Edit any incident
- `incident.delete` - Delete incidents
- `incident.verify` - Verify incidents
- `incident.moderate` - Moderate content
- `incident.publish` - Publish incidents

**User Management (5):**
- `user.read` - View user profiles
- `user.update` - Edit user information
- `user.delete` - Delete user accounts
- `user.manage_roles` - Assign/remove user roles
- `user.verify` - Verify user accounts

**Alert Management (5):**
- `alert.create` - Create alerts
- `alert.read` - View alerts
- `alert.update` - Edit alerts
- `alert.delete` - Delete alerts
- `alert.broadcast` - Broadcast alerts to public

**Report & Analytics (7):**
- `report.create` - Generate reports
- `report.read` - View reports
- `report.export` - Export data
- `report.analyze` - Perform analysis
- `analytics.view` - View dashboards
- `analytics.export` - Export analytics
- `analytics.create_dashboard` - Create dashboards

**System Management (3):**
- `system.configure` - Configure settings
- `system.audit` - View audit logs
- `system.manage_settings` - Manage system-wide settings

---

### 6. Super Administrator (super_admin)
**Description**: Ultimate system control with all permissions
**Permission Count**: 29 (all permissions)
**Use Case**: System owners and developers with full access

**Additional Permissions** (beyond admin):
- `user.impersonate` - Impersonate users for support
- `system.backup` - Manage system backups

---

## Permissions Reference

### Incident Permissions (7)
| Permission | Resource | Action | Description |
|------------|----------|--------|-------------|
| incident.create | incident | create | Create new security incidents |
| incident.read | incident | read | View security incidents |
| incident.update | incident | update | Edit security incidents |
| incident.delete | incident | delete | Delete security incidents |
| incident.verify | incident | verify | Verify incident authenticity |
| incident.moderate | incident | moderate | Moderate incident content |
| incident.publish | incident | publish | Publish incidents to public |

### User Permissions (6)
| Permission | Resource | Action | Description |
|------------|----------|--------|-------------|
| user.read | user | read | View user profiles |
| user.update | user | update | Update user information |
| user.delete | user | delete | Delete user accounts |
| user.manage_roles | user | manage_roles | Assign and remove user roles |
| user.impersonate | user | impersonate | Impersonate users for support |
| user.verify | user | verify | Verify user accounts |

### Alert Permissions (5)
| Permission | Resource | Action | Description |
|------------|----------|--------|-------------|
| alert.create | alert | create | Create security alerts |
| alert.read | alert | read | View security alerts |
| alert.update | alert | update | Edit security alerts |
| alert.delete | alert | delete | Delete security alerts |
| alert.broadcast | alert | broadcast | Broadcast alerts to public |

### Report Permissions (4)
| Permission | Resource | Action | Description |
|------------|----------|--------|-------------|
| report.create | report | create | Generate reports |
| report.read | report | read | View reports |
| report.export | report | export | Export reports |
| report.analyze | report | analyze | Perform data analysis |

### Analytics Permissions (3)
| Permission | Resource | Action | Description |
|------------|----------|--------|-------------|
| analytics.view | analytics | view | View analytics dashboards |
| analytics.export | analytics | export | Export analytics data |
| analytics.create_dashboard | analytics | create_dashboard | Create custom dashboards |

### System Permissions (4)
| Permission | Resource | Action | Description |
|------------|----------|--------|-------------|
| system.configure | system | configure | Configure system settings |
| system.audit | system | audit | View audit logs |
| system.backup | system | backup | Manage system backups |
| system.manage_settings | system | manage_settings | Manage system-wide settings |

---

## Database Schema

### Tables

**roles**
```sql
id              UUID PRIMARY KEY
name            VARCHAR(50) UNIQUE NOT NULL
display_name    VARCHAR(100) NOT NULL
description     TEXT
is_system_role  BOOLEAN DEFAULT FALSE
created_at      TIMESTAMP WITH TIMEZONE
updated_at      TIMESTAMP WITH TIMEZONE
```

**permissions**
```sql
id          UUID PRIMARY KEY
name        VARCHAR(100) UNIQUE NOT NULL
resource    VARCHAR(50) NOT NULL
action      VARCHAR(50) NOT NULL
description TEXT
created_at  TIMESTAMP WITH TIMEZONE
```

**role_permissions** (Many-to-Many)
```sql
role_id         UUID REFERENCES roles(id) ON DELETE CASCADE
permission_id   UUID REFERENCES permissions(id) ON DELETE CASCADE
PRIMARY KEY (role_id, permission_id)
```

**user_roles** (Many-to-Many)
```sql
user_id      UUID REFERENCES users(id) ON DELETE CASCADE
role_id      UUID REFERENCES roles(id) ON DELETE CASCADE
assigned_by  UUID REFERENCES users(id)
assigned_at  TIMESTAMP WITH TIMEZONE
expires_at   TIMESTAMP WITH TIMEZONE
PRIMARY KEY (user_id, role_id)
```

---

## Usage Examples

### Checking User Permissions in Code

```python
from app.api.dependencies.auth import has_permission

# In an endpoint
def verify_incident(incident_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Check if user has permission
    if not has_permission(current_user, "incident.verify", db):
        raise HTTPException(403, "Missing permission: incident.verify")

    # Proceed with verification
    ...
```

### Using Permission Dependencies

```python
from app.api.dependencies.auth import require_permissions

# Require specific permissions
@router.post("/incidents/verify")
async def verify_incident(
    incident_id: str,
    current_user: User = Depends(require_permissions("incident.verify"))
):
    # User has been verified to have incident.verify permission
    ...
```

### Using Role Dependencies

```python
from app.api.dependencies.auth import require_roles

# Require specific role
@router.get("/admin/dashboard")
async def admin_dashboard(
    current_user: User = Depends(require_roles("admin", "super_admin"))
):
    # User has either admin or super_admin role
    ...
```

### Assigning Roles to Users

```python
# Via database
from app.models.auth import user_roles

# Assign moderator role to user
moderator_role = db.query(Role).filter_by(name="moderator").first()
db.execute(
    user_roles.insert().values(
        user_id=user.id,
        role_id=moderator_role.id,
        assigned_by=admin_user.id
    )
)
db.commit()
```

---

## Seeding the Database

The system includes a seed script to populate roles and permissions:

```bash
cd nigeria-security-system/backend
python seed_roles_permissions.py
```

**Output:**
- Creates 29 permissions across 6 resources
- Creates 6 system roles with appropriate permission assignments
- Can be run multiple times (idempotent - won't create duplicates)
- Shows detailed output of what was created

---

## Security Considerations

### System Roles
- All default roles are marked as `is_system_role = True`
- System roles cannot be deleted through the API
- Prevents accidental removal of critical roles

### Permission Granularity
- Permissions follow the `resource.action` naming convention
- Each permission represents a single capability
- Allows for fine-grained access control
- Easy to audit and understand

### Role Hierarchy
While roles don't have explicit parent-child relationships, they follow a logical hierarchy:
```
user < verified_reporter < moderator < analyst < admin < super_admin
```

### Best Practices
1. **Principle of Least Privilege**: Assign users the minimum role needed for their tasks
2. **Regular Audits**: Use `system.audit` permission to review role assignments
3. **Time-Limited Roles**: Use `expires_at` in `user_roles` for temporary access
4. **Trust Score Integration**: Monitor user behavior and adjust roles accordingly
5. **Email Verification**: Require email verification before role elevation

---

## API Endpoints (Future)

The following endpoints will be implemented for role management:

- `GET /api/v1/admin/roles` - List all roles
- `GET /api/v1/admin/roles/{role_id}` - Get role details with permissions
- `POST /api/v1/admin/users/{user_id}/roles` - Assign role to user
- `DELETE /api/v1/admin/users/{user_id}/roles/{role_id}` - Remove role from user
- `GET /api/v1/admin/permissions` - List all permissions
- `GET /api/v1/auth/me/permissions` - Get current user's permissions

---

## Testing

Run the RBAC verification test:

```bash
cd nigeria-security-system/backend
python test_rbac_system.py
```

**Tests Performed:**
1. Verify all roles exist in database
2. Verify all permissions exist
3. Verify role-permission associations
4. Test user registration with role assignment
5. Test login with roles returned in response

**Expected Result:** All tests pass, confirming RBAC system is working correctly

---

## Maintenance

### Adding New Permissions

1. Add permission to `PERMISSIONS` list in `seed_roles_permissions.py`
2. Assign to appropriate roles in `ROLES` list
3. Run seed script: `python seed_roles_permissions.py`
4. Update this documentation

### Adding New Roles

1. Add role to `ROLES` list in `seed_roles_permissions.py`
2. Assign appropriate permissions
3. Run seed script
4. Update this documentation
5. Consider hierarchy and security implications

### Removing Permissions

**Warning**: Removing permissions can break existing code. Instead:
1. Mark permission as deprecated in description
2. Remove from role assignments
3. Update code to not use the permission
4. Only delete after ensuring no references exist

---

## Migration History

- **2025-11-21**: Initial RBAC system implementation
  - Created roles and permissions tables
  - Created role_permissions and user_roles junction tables
  - Seeded 6 default roles with 29 permissions
  - Implemented permission checking dependencies

---

## Troubleshooting

### Users Don't Have Expected Roles
- Check `user_roles` table for role assignments
- Verify role assignment succeeded (check for foreign key errors)
- Ensure user ID and role ID are correct UUIDs

### Permission Checks Failing
- Verify permission exists in database: `SELECT * FROM permissions WHERE name = 'permission.name'`
- Check role has permission: `SELECT * FROM role_permissions WHERE role_id = '...'`
- Verify user has role: `SELECT * FROM user_roles WHERE user_id = '...'`

### Seed Script Errors
- Ensure database is running: `docker ps | grep nigeria-security-db`
- Check database connection in `.env` file
- Verify migrations are applied: `alembic current`
- Check for unique constraint violations (permissions/roles may already exist)

---

## Future Enhancements

1. **Dynamic Role Creation**: Allow admins to create custom roles via API
2. **Permission Templates**: Predefined permission sets for common role types
3. **Role Inheritance**: Define parent-child relationships between roles
4. **Temporal Permissions**: Time-based permission grants
5. **Geo-Based Permissions**: Permissions based on user location
6. **Resource-Level Permissions**: Permissions for specific incidents/alerts (e.g., "can edit own incidents")

---

**Document Version**: 1.0
**Last Updated**: November 21, 2025
**Maintained By**: Development Team
