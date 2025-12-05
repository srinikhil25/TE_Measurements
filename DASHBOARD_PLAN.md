# Dashboard Implementation Plan

## Overview
Different dashboards for Admin and Researcher roles with role-based access control.

## User Roles

### Admin User
- **Username**: `admin`
- **Password**: `admin`
- **Access**: Full system access, user management, view all data

### Researcher User
- **Username**: `researcher`
- **Password**: `researcher`
- **Access**: Own workbooks and measurements only

---

## Dashboard Structure

### 1. Admin Dashboard

#### Features:
- **User Management Panel**
  - List all users (admin + researchers)
  - Create new users (researchers only)
  - Edit user details (name, email, role)
  - Activate/Deactivate users
  - Reset passwords
  - View user statistics (number of workbooks, measurements)

- **System Overview**
  - Total users count
  - Total workbooks count (all users) 
  - Total measurements count (all users)
  - Recent activity log
  - System statistics

- **All Workbooks View**
  - View all workbooks from all researchers
  - Filter by researcher
  - Search workbooks
  - View workbook details
  - Export data (all or filtered)

- **All Measurements View**
  - View all measurements from all researchers
  - Filter by researcher, workbook, measurement type
  - Search measurements
  - View measurement details
  - Export data

- **Navigation**
  - User Management tab
  - System Overview tab
  - All Workbooks tab
  - All Measurements tab
  - Settings (if needed)

#### Layout:
```
┌─────────────────────────────────────────┐
│  TE Measurements - Admin Dashboard      │
├─────────────────────────────────────────┤
│  [User Mgmt] [Overview] [Workbooks]    │
│  [Measurements] [Settings]               │
├─────────────────────────────────────────┤
│                                         │
│  [Selected Tab Content]                 │
│                                         │
└─────────────────────────────────────────┘
```

---

### 2. Researcher Dashboard

#### Features:
- **My Workbooks Panel**
  - List all workbooks created by the researcher
  - Create new workbook button (prominent)
  - Edit workbook details
  - Delete workbook (with confirmation)
  - View workbook statistics (number of measurements)

- **Recent Measurements**
  - Show last 5-10 recent measurements
  - Quick view of measurement status
  - Link to full measurement details

- **Quick Actions**
  - Create New Workbook (if no workbooks exist, show prominently)
  - Start New Measurement (if workbooks exist)
  - View Recent Data

- **Empty State**
  - If no workbooks: Show "Create Your First Workbook" with large button
  - If workbooks but no measurements: Show "Start Your First Measurement"

#### Layout:
```
┌─────────────────────────────────────────┐
│  TE Measurements - Welcome, [Name]      │
├─────────────────────────────────────────┤
│  [My Workbooks] [Recent Measurements]   │
├─────────────────────────────────────────┤
│                                         │
│  [Workbooks List / Empty State]         │
│                                         │
│  [+ Create New Workbook]                │
│                                         │
└─────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Dashboard Routing & Navigation
- [ ] Create dashboard router/navigation system
- [ ] Implement role detection from JWT token
- [ ] Route to appropriate dashboard based on role
- [ ] Create navigation bar/header component

### Phase 2: Researcher Dashboard
- [ ] Create workbook list view
- [ ] Implement empty state (no workbooks)
- [ ] Create workbook creation form
- [ ] Add recent measurements widget
- [ ] Implement workbook card/list UI

### Phase 3: Admin Dashboard
- [ ] Create user management panel
- [ ] Implement user list with actions
- [ ] Create user creation/edit forms
- [ ] Add system overview statistics
- [ ] Create all workbooks view (with filters)
- [ ] Create all measurements view (with filters)

### Phase 4: API Endpoints
- [ ] GET /api/users (admin only) - List all users
- [ ] POST /api/users (admin only) - Create user
- [ ] PUT /api/users/{id} (admin only) - Update user
- [ ] DELETE /api/users/{id} (admin only) - Deactivate user
- [ ] GET /api/users/me - Get current user info
- [ ] GET /api/workbooks - List user's workbooks (filtered by role)
- [ ] POST /api/workbooks - Create workbook
- [ ] GET /api/workbooks/all (admin only) - List all workbooks

### Phase 5: Workbook Management
- [ ] Workbook creation form
- [ ] Workbook edit form
- [ ] Workbook deletion (with confirmation)
- [ ] Workbook detail view

---

## UI Components to Create

### Shared Components
- `NavigationBar` - Top navigation with role-based menu
- `UserProfile` - User info display
- `LogoutButton` - Logout functionality

### Researcher Components
- `WorkbookList` - List of researcher's workbooks
- `WorkbookCard` - Individual workbook card
- `CreateWorkbookForm` - Form to create new workbook
- `RecentMeasurements` - Widget showing recent measurements
- `EmptyState` - Empty state when no workbooks

### Admin Components
- `UserManagementPanel` - User CRUD operations
- `UserList` - Table/list of all users
- `UserForm` - Create/edit user form
- `SystemOverview` - Statistics and overview
- `AllWorkbooksView` - View all workbooks with filters
- `AllMeasurementsView` - View all measurements with filters

---

## Data Flow

### Login → Dashboard Routing
```
Login Success
    ↓
Extract role from JWT token
    ↓
Route to:
    - Admin → Admin Dashboard
    - Researcher → Researcher Dashboard
```

### Researcher Workflow
```
Dashboard → View Workbooks
    ↓
Create Workbook → Fill form → Save
    ↓
Select Workbook → Choose Measurement Type
    ↓
Start Measurement → Run measurement session
    ↓
View Results → Export Data
```

### Admin Workflow
```
Dashboard → Select Tab
    ↓
User Management → Create/Edit Users
    OR
System Overview → View Statistics
    OR
All Workbooks → View/Filter All Data
    OR
All Measurements → View/Filter All Data
```

---

## Security Considerations

1. **Role-based routing**: Check role before showing dashboard
2. **API protection**: All endpoints check user role
3. **Data isolation**: Researchers only see their own data
4. **Admin access**: Admins can see all data but with clear indication

---

## Next Steps

1. ✅ Create researcher user in database
2. Update login to route to appropriate dashboard
3. Create dashboard base structure
4. Implement researcher dashboard first (simpler)
5. Implement admin dashboard
6. Add API endpoints for user management
7. Test with both user types

