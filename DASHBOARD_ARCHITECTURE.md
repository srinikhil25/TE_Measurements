# Dashboard Architecture - Multi-Role Design

## Overview

The TE Measurements application uses a **role-based multi-dashboard architecture** where each user role (Researcher, Lab Admin, Super Admin) has a completely separate, specialized dashboard interface.

## Design Pattern: Inheritance with Base Class

### Architecture Layers

```
BaseDashboard (Abstract Base)
    ├── ResearcherDashboard
    ├── LabAdminDashboard
    └── SuperAdminDashboard
```

### Key Design Principles

1. **Separation of Concerns**: Each dashboard is a separate class focused on its role's specific needs
2. **Code Reusability**: Common functionality (header, logout, session management) in base class
3. **Extensibility**: Easy to add new roles or modify existing ones
4. **Maintainability**: Changes to one dashboard don't affect others

## Base Dashboard Class

**Location**: `src/gui/base_dashboard.py`

### Responsibilities

- Common UI elements (header, welcome message, logout button)
- Session management
- User information display
- Role badge display
- Common layout structure

### Key Methods

```python
class BaseDashboard(QWidget):
    def _setup_base_ui(self)          # Initialize common UI
    def _create_header(self)          # Create header with logout
    def _create_role_badge(self)       # Override for custom badges
    def update_header(self)            # Update with user info
    def load_data(self)                # Override in subclasses
    def get_current_user(self)         # Get logged-in user
```

## Role-Specific Dashboards

### 1. Researcher Dashboard

**File**: `src/gui/researcher_dashboard.py`

**Features**:
- Workbook management (create, view, edit)
- Measurement taking interface
- View own measurements only
- Three measurement pages per workbook (Seebeck, Resistivity, Thermal Conductivity)

**UI Components**:
- Workbooks table
- Workbook creation dialog
- Measurement viewer/editor with tabs

### 2. Lab Admin Dashboard

**File**: `src/gui/lab_admin_dashboard.py`

**Features**:
- View all researchers in their lab
- View all workbooks from lab researchers
- Comment on researchers' work
- Statistics and analytics for lab
- Date range filtering

**UI Components**:
- Researchers table
- Statistics dashboard
- Workbook viewer (read-only)
- Comment interface

### 3. Super Admin Dashboard

**File**: `src/gui/super_admin_dashboard.py`

**Features**:
- System-wide statistics
- Lab management (create, edit, delete)
- User management (create, edit, delete, assign to labs)
- Audit log viewer
- Instrument usage logs

**UI Components**:
- Statistics dashboard tab
- Labs management tab
- Users management tab
- Audit logs tab

## Dashboard Factory

**Location**: `src/gui/dashboard_factory.py`

### Purpose

Centralized creation of dashboards based on user role. Provides:
- Type-safe dashboard creation
- Easy role-to-dashboard mapping
- Single point of change for dashboard instantiation

### Usage

```python
from src.gui.dashboard_factory import DashboardFactory
from src.models import UserRole

# Create dashboard based on role
dashboard = DashboardFactory.create_dashboard(UserRole.RESEARCHER, parent)
```

## Main Window Integration

**Location**: `src/gui/main_window.py`

### Dashboard Switching

The main window uses a `QStackedWidget` to switch between dashboards:

```python
# All dashboards created at startup
self.researcher_dashboard = ResearcherDashboard(self)
self.lab_admin_dashboard = LabAdminDashboard(self)
self.super_admin_dashboard = SuperAdminDashboard(self)

# Switch based on role
def show_dashboard_for_user(self, user):
    if user.role == UserRole.RESEARCHER:
        self.stacked_widget.setCurrentWidget(self.researcher_dashboard)
    # ... etc
```

### Benefits of This Approach

1. **Lazy Loading**: Dashboards are created once, reused
2. **State Preservation**: Dashboard state maintained when switching
3. **Fast Switching**: No recreation overhead

## Data Flow

```
Login → Authentication → Role Detection → Dashboard Selection → Data Loading
                                                                    ↓
                                                          Role-Specific UI
```

## Access Control Integration

Each dashboard enforces access control:

- **Researcher**: Can only access own workbooks (enforced in services)
- **Lab Admin**: Can access all lab workbooks (read-only)
- **Super Admin**: Full system access

Access control is enforced at:
1. **Service Layer**: `WorkbookService`, `MeasurementService`
2. **Auth Manager**: `AuthManager.can_access_*()` methods
3. **UI Layer**: Dashboards only show accessible data

## Customization Points

### Adding a New Role

1. Create new dashboard class inheriting from `BaseDashboard`
2. Implement role-specific UI in `init_ui()`
3. Override `load_data()` for data loading
4. Add to `DashboardFactory`
5. Add to `MainWindow.show_dashboard_for_user()`

### Customizing Base Functionality

- Override `_create_role_badge()` for custom badges
- Override `_get_role_display_name()` for custom role names
- Extend `BaseDashboard` for shared functionality

## Best Practices

1. **Keep Dashboards Focused**: Each dashboard should only contain functionality relevant to its role
2. **Use Services Layer**: Business logic in services, not dashboards
3. **Consistent UI**: Use base class for common UI elements
4. **Error Handling**: Handle errors gracefully in each dashboard
5. **Data Refresh**: Implement `refresh()` method for manual updates

## Performance Considerations

- Dashboards are created once at startup (not on each login)
- Data loading is lazy (only when dashboard is shown)
- Use `load_data()` to refresh when needed
- Consider pagination for large datasets

## Future Enhancements

- Dashboard plugins/extensions
- Customizable dashboard layouts
- Dashboard themes
- Export dashboard configurations
- Dashboard analytics

