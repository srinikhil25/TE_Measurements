# TE Measurements - Architecture Documentation

## Overview

TE Measurements is a desktop application built with PyQt6 for managing Seebeck measurements, electrical resistivity, and thermal conductivity data with strict multi-tenant access control.

## Architecture Layers

### 1. Presentation Layer (GUI)
- **Location**: `src/gui/`
- **Framework**: PyQt6
- **Components**:
  - `main_window.py`: Main application window with role-based dashboard switching
  - `login_window.py`: Authentication interface
  - `researcher_dashboard.py`: Researcher workspace
  - `lab_admin_dashboard.py`: Lab administrator interface
  - `super_admin_dashboard.py`: System administration interface

### 2. Business Logic Layer (Services)
- **Location**: `src/services/`
- **Components**:
  - `workbook_service.py`: Workbook CRUD operations with access control
  - `measurement_service.py`: Measurement creation and retrieval (immutable data)
  - `statistics_service.py`: Statistics and reporting generation

### 3. Data Access Layer (Models)
- **Location**: `src/models/`
- **ORM**: SQLAlchemy
- **Models**:
  - `User`: User accounts with role-based access
  - `Lab`: Lab organization units
  - `Workbook`: Experiment containers (one per sample)
  - `Measurement`: Immutable instrument data (Seebeck, Resistivity, Thermal Conductivity)
  - `Comment`: Lab admin comments on workbooks
  - `AuditLog`: System audit trail

### 4. Authentication & Authorization
- **Location**: `src/auth/`
- **Components**:
  - `auth_manager.py`: Authentication and permission checking
  - `session.py`: Session management

### 5. Instrument Integration
- **Location**: `src/instruments/`
- **Components**:
  - `keithley_connection.py`: Interface for Keithley instrument (to be integrated)

### 6. Utilities
- **Location**: `src/utils/`
- **Components**:
  - `config_loader.py`: Configuration management

## Database Schema

### Core Entities

```
User (id, username, email, password_hash, role, lab_id, ...)
  ├── Lab (id, name, admin_id, ...)
  ├── Workbook (id, title, researcher_id, lab_id, ...)
  │   ├── Measurement (id, workbook_id, measurement_type, raw_data_path, parsed_data, ...)
  │   └── Comment (id, workbook_id, author_id, content, ...)
  └── AuditLog (id, user_id, action_type, ...)
```

### Access Control Model

1. **Researcher**: Can only access own workbooks
2. **Lab Admin**: Can view all workbooks in their lab, can comment
3. **Super Admin**: Full system access

## Data Flow

### Measurement Workflow

1. Researcher creates a workbook
2. Researcher connects to instrument (via GUI)
3. Researcher selects measurement type (Seebeck/Resistivity/Thermal Conductivity)
4. Instrument takes measurement
5. Raw data saved to external drive
6. Data parsed and stored in database
7. Measurement appears in workbook's appropriate "page"

### Access Control Flow

1. User authenticates via `AuthManager`
2. Session created via `SessionManager`
3. All data access checked via `AuthManager.can_access_*()` methods
4. Service layer enforces permissions
5. GUI reflects user's permissions

## Security Features

1. **Password Hashing**: bcrypt with salt
2. **Immutable Data**: Instrument measurements cannot be edited
3. **Row-Level Security**: Lab-based data isolation
4. **Audit Logging**: All actions logged
5. **Session Management**: Secure session handling
6. **Account Lockout**: Failed login attempt tracking

## Storage Architecture

- **Database**: Structured data (PostgreSQL/SQLite)
- **File System**: Raw measurement files on external drive
- **Backup**: Configurable backup location

## Workbook Structure

Each workbook represents one experiment on one sample and contains:
- **Page 1**: Seebeck measurements
- **Page 2**: Resistivity measurements
- **Page 3**: Thermal conductivity measurements

Each page can contain multiple measurements (time series, different conditions, etc.)

## Extension Points

1. **Instrument Integration**: Implement `KeithleyConnection` class
2. **Data Parsing**: Extend `MeasurementService._calculate_statistics()`
3. **Statistics**: Extend `StatisticsService` for custom reports
4. **Export**: Add export functionality to services layer

## Deployment Considerations

- **Single Machine**: Application runs on dedicated CPU connected to instrument
- **Database**: Local PostgreSQL or SQLite
- **Storage**: External harddisk for raw data
- **Multi-User**: Multiple users can run application, database enforces isolation

## Future Enhancements

1. Data export (CSV, Excel, JSON)
2. Advanced plotting/visualization
3. Measurement templates
4. Automated backup
5. Network deployment (optional)
6. API for external integrations

