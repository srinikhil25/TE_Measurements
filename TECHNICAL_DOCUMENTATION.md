# TE Measurements - Technical Documentation

**Version:** 1.0.0  
**Last Updated:** December 2024  
**Document Type:** Technical Specification & Architecture Documentation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture](#architecture)
4. [Database Schema](#database-schema)
5. [Authentication & Authorization](#authentication--authorization)
6. [User Roles & Permissions](#user-roles--permissions)
7. [Features by Role](#features-by-role)
8. [Internationalization (i18n)](#internationalization-i18n)
9. [Services Layer](#services-layer)
10. [User Interface Design](#user-interface-design)
11. [Configuration Management](#configuration-management)
12. [Deployment](#deployment)
13. [Development Setup](#development-setup)
14. [Security Considerations](#security-considerations)
15. [Future Enhancements](#future-enhancements)

---

## Executive Summary

**TE Measurements** is a professional desktop application designed for researchers to measure and manage Seebeck effect, electrical resistivity, and thermal conductivity data. The system provides strict multi-tenant access control, role-based permissions, and comprehensive data management capabilities for research laboratories.

### Key Features
- Multi-lab environment with strict data isolation
- Role-based access control (Researcher, Lab Admin, Super Admin)
- Immutable measurement data storage
- Internationalization support (English/Japanese)
- On-premises deployment with instrument integration
- Comprehensive audit logging

---

## System Overview

### Technology Stack

| Component | Technology |
|-----------|-----------|
| **Frontend Framework** | PyQt6 (Cross-platform desktop GUI) |
| **Backend Language** | Python 3.8+ |
| **ORM** | SQLAlchemy 2.0+ |
| **Database** | PostgreSQL (primary) / SQLite (fallback) |
| **Password Hashing** | bcrypt |
| **Configuration** | ConfigParser (INI format) |

### System Requirements

- **Operating System:** Windows 10+ / Linux (Ubuntu 20.04+)
- **Python:** 3.8 or higher
- **Database:** PostgreSQL 12+ (recommended) or SQLite 3.30+
- **RAM:** Minimum 4GB, Recommended 8GB
- **Storage:** Minimum 10GB free space
- **Display:** 1280x720 minimum resolution

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TE Measurements Application               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │   GUI Layer  │    │ Service Layer│    │  Data Layer  │   │
│  │  (PyQt6)     │◄───│  (Business   │◄───│ (SQLAlchemy) │   │
│  │              │    │   Logic)     │    │              │   │
│  └──────────────┘    └──────────────┘    └──────────────┘   │
│         │                   │                   │            │
│         └───────────────────┴───────────────────┘            │
│                           │                                   │
│                    ┌───────▼───────┐                          │
│                    │   PostgreSQL  │                          │
│                    │   Database    │                          │
│                    └───────────────┘                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### 1. **Presentation Layer (GUI)**
- **Location:** `src/gui/`
- **Components:**
  - `main_window.py` - Application entry point and window management
  - `login_window.py` - Authentication interface
  - `base_dashboard.py` - Base class for all role dashboards
  - `researcher_dashboard.py` - Researcher-specific dashboard
  - `lab_admin_dashboard.py` - Lab administrator dashboard
  - `super_admin_dashboard.py` - Super administrator dashboard
  - `workbook_window.py` - Workbook viewing/editing interface
  - `dialogs/` - Modal dialogs for user/lab management

#### 2. **Business Logic Layer (Services)**
- **Location:** `src/services/`
- **Components:**
  - `workbook_service.py` - Workbook CRUD operations
  - `measurement_service.py` - Measurement data management
  - `user_service.py` - User management (super admin only)
  - `statistics_service.py` - Analytics and reporting

#### 3. **Data Access Layer (Models)**
- **Location:** `src/models/`
- **Components:**
  - `user.py` - User model with role-based access control
  - `lab.py` - Laboratory model
  - `workbook.py` - Workbook/experiment model
  - `measurement.py` - Measurement data model
  - `comment.py` - Comment model for lab admin feedback
  - `audit_log.py` - Audit trail model
  - `associations.py` - Many-to-many relationship tables

#### 4. **Authentication & Authorization**
- **Location:** `src/auth/`
- **Components:**
  - `auth_manager.py` - Authentication logic
  - `session.py` - Session management with language preference

#### 5. **Internationalization**
- **Location:** `src/i18n/`
- **Components:**
  - `__init__.py` - Translation manager
  - `translations/en.json` - English translations
  - `translations/ja.json` - Japanese translations

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│    User     │────────▶│     Lab     │◀────────│    User     │
│             │ lab_id  │             │ admin_id│  (Admin)    │
└─────────────┘         └─────────────┘         └─────────────┘
     │                        │
     │                        │
     │ researcher_id          │ lab_id
     │                        │
     ▼                        ▼
┌─────────────┐         ┌─────────────┐
│  Workbook   │────────▶│ Measurement │
│             │         │             │
└─────────────┘         └─────────────┘
     │
     │ workbook_id
     │
     ▼
┌─────────────┐
│   Comment   │
│             │
└─────────────┘

┌─────────────┐
│ Audit Log   │
│             │
└─────────────┘
```

### Core Tables

#### 1. **users**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique user identifier |
| username | VARCHAR(100) | UNIQUE, NOT NULL | Login username |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| full_name | VARCHAR(255) | NOT NULL | User's full name |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| role | ENUM | NOT NULL | User role (researcher/lab_admin/super_admin) |
| preferred_language | VARCHAR(10) | NOT NULL, DEFAULT 'en' | UI language preference |
| lab_id | INTEGER | FOREIGN KEY | Primary lab association |
| is_active | BOOLEAN | DEFAULT TRUE | Account status |
| is_locked | BOOLEAN | DEFAULT FALSE | Account lock status |
| failed_login_attempts | INTEGER | DEFAULT 0 | Failed login counter |
| last_login | TIMESTAMP | NULLABLE | Last login timestamp |
| created_at | TIMESTAMP | NOT NULL | Account creation time |
| updated_at | TIMESTAMP | NULLABLE | Last update time |

#### 2. **labs**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique lab identifier |
| name | VARCHAR(255) | UNIQUE, NOT NULL | Lab name |
| description | VARCHAR(1000) | NULLABLE | Lab description |
| location | VARCHAR(255) | NULLABLE | Physical location |
| admin_id | INTEGER | FOREIGN KEY | Primary lab administrator |
| is_active | BOOLEAN | DEFAULT TRUE | Lab status |
| created_at | TIMESTAMP | NOT NULL | Lab creation time |
| updated_at | TIMESTAMP | NULLABLE | Last update time |

#### 3. **workbooks**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique workbook identifier |
| title | VARCHAR(255) | NOT NULL | Workbook title |
| description | TEXT | NULLABLE | Workbook description |
| sample_name | VARCHAR(255) | NULLABLE | Sample identifier |
| sample_id | VARCHAR(100) | NULLABLE | Sample ID |
| researcher_id | INTEGER | FOREIGN KEY, NOT NULL | Owner researcher |
| lab_id | INTEGER | FOREIGN KEY, NOT NULL | Associated lab |
| is_active | BOOLEAN | DEFAULT TRUE | Workbook status |
| created_at | TIMESTAMP | NOT NULL | Creation time |
| updated_at | TIMESTAMP | NULLABLE | Last update time |
| last_measurement_at | TIMESTAMP | NULLABLE | Last measurement time |

#### 4. **measurements**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique measurement identifier |
| workbook_id | INTEGER | FOREIGN KEY, NOT NULL | Parent workbook |
| measurement_type | ENUM | NOT NULL | Type (seebeck/resistivity/thermal) |
| raw_data | JSON | NOT NULL | Raw instrument data |
| parsed_data | JSON | NULLABLE | Processed measurement data |
| notes | TEXT | NULLABLE | Measurement notes |
| created_at | TIMESTAMP | NOT NULL | Measurement time |
| created_by | INTEGER | FOREIGN KEY | User who created measurement |

#### 5. **comments**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique comment identifier |
| workbook_id | INTEGER | FOREIGN KEY, NOT NULL | Target workbook |
| author_id | INTEGER | FOREIGN KEY, NOT NULL | Lab admin who commented |
| content | TEXT | NOT NULL | Comment text |
| is_resolved | BOOLEAN | DEFAULT FALSE | Resolution status |
| created_at | TIMESTAMP | NOT NULL | Comment time |
| updated_at | TIMESTAMP | NULLABLE | Last update time |

#### 6. **audit_logs**
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique log entry identifier |
| user_id | INTEGER | FOREIGN KEY, NULLABLE | User who performed action |
| action_type | ENUM | NOT NULL | Action type (login, create, etc.) |
| description | TEXT | NULLABLE | Action description |
| entity_type | VARCHAR(50) | NULLABLE | Affected entity type |
| entity_id | INTEGER | NULLABLE | Affected entity ID |
| additional_metadata | JSON | NULLABLE | Additional context |
| ip_address | VARCHAR(45) | NULLABLE | User IP address |
| user_agent | VARCHAR(500) | NULLABLE | User agent string |
| created_at | TIMESTAMP | NOT NULL | Log entry time |

### Association Tables

#### **user_lab_permissions**
Many-to-many relationship for researchers with multi-lab access.

| Column | Type | Constraints |
|--------|------|-------------|
| user_id | INTEGER | FOREIGN KEY, PRIMARY KEY |
| lab_id | INTEGER | FOREIGN KEY, PRIMARY KEY |

---

## Authentication & Authorization

### Authentication Flow

```
┌──────────┐      ┌──────────────┐      ┌─────────────┐
│  User    │─────▶│ Login Window │─────▶│ AuthManager │
│          │      │              │      │             │
└──────────┘      └──────────────┘      └──────┬──────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │   Database  │
                                         │   (Verify   │
                                         │  Password)  │
                                         └──────┬──────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │  Session    │
                                         │  Manager    │
                                         │ (Set User + │
                                         │  Language)  │
                                         └──────┬──────┘
                                                │
                                                ▼
                                         ┌─────────────┐
                                         │ Dashboard   │
                                         │ (Role-based)│
                                         └─────────────┘
```

### Password Security

- **Hashing Algorithm:** bcrypt with automatic salt generation
- **Minimum Length:** 8 characters (enforced during user creation)
- **Password Generation:** Auto-generated unique alphanumeric passwords (8-16 chars) for new users
- **Password Reset:** Super admin can reset passwords (generates new unique password)
- **Account Lockout:** Automatic lockout after 5 failed login attempts (configurable)

### Session Management

- **Session Type:** In-memory singleton (CurrentSession)
- **Session Data:**
  - Current user object
  - Current lab context
  - Preferred language
- **Session Lifecycle:**
  - Created on successful login
  - Cleared on logout or application exit
  - Language preference loaded from user's `preferred_language` field

---

## User Roles & Permissions

### Role Hierarchy

```
Super Admin (Highest Privilege)
    │
    ├── Lab Admin
    │       │
    │       └── Researcher (Base Role)
    │
    └── Researcher (Direct Assignment)
```

### Role Definitions

#### 1. **Researcher**
- **Primary Function:** Create and manage workbooks, perform measurements
- **Permissions:**
  - ✅ Create multiple workbooks
  - ✅ Edit workbook metadata (title, sample name)
  - ✅ Delete own workbooks (soft delete)
  - ✅ View own workbooks and measurements
  - ❌ View other researchers' data
  - ❌ Edit measurement data (immutable)
  - ❌ Create/delete other users
- **Lab Association:** Belongs to one primary lab (can have multi-lab permissions)

#### 2. **Lab Admin**
- **Primary Function:** Oversee lab researchers, review work, provide feedback
- **Permissions:**
  - ✅ View all researchers in their lab
  - ✅ View all workbooks from lab researchers
  - ✅ Comment on researchers' workbooks
  - ✅ View lab statistics and activity logs
  - ✅ See researcher activity status
  - ❌ Edit or delete researcher data
  - ❌ Create/delete users
  - ❌ Access other labs' data
- **Lab Association:** Administers one lab

#### 3. **Super Admin**
- **Primary Function:** System administration, user/lab management
- **Permissions:**
  - ✅ Create/delete labs
  - ✅ Create/delete users (all roles)
  - ✅ Edit user details (role, lab, status)
  - ✅ Reset user passwords
  - ✅ View system-wide statistics
  - ✅ View all audit logs
  - ✅ Access all labs and workbooks
  - ❌ Edit measurement data (immutable for all roles)

### Access Control Matrix

| Action | Researcher | Lab Admin | Super Admin |
|--------|-----------|-----------|-------------|
| Create Workbook | ✅ Own | ❌ | ❌ |
| Edit Own Workbook | ✅ | ❌ | ❌ |
| Delete Own Workbook | ✅ | ❌ | ❌ |
| View Own Workbooks | ✅ | ❌ | ❌ |
| View Lab Workbooks | ❌ | ✅ | ✅ |
| View All Workbooks | ❌ | ❌ | ✅ |
| Comment on Workbook | ❌ | ✅ | ✅ |
| Create User | ❌ | ❌ | ✅ |
| Edit User | ❌ | ❌ | ✅ |
| Create Lab | ❌ | ❌ | ✅ |
| View Statistics | ❌ | ✅ (Lab) | ✅ (System) |
| View Audit Logs | ❌ | ❌ | ✅ |

---

## Features by Role

### Researcher Dashboard

#### Core Features
1. **Workbook Management**
   - Grid view of all workbooks (card-based layout)
   - Search workbooks by title
   - Create new workbook
   - Inline title editing
   - Delete workbook (via overflow menu)

2. **Workbook View**
   - Full-screen window
   - Three tabs (bottom, Excel-style):
     - Seebeck Measurement
     - Electrical Resistivity
     - Thermal Conductivity
   - Measurement data display (read-only)

3. **Data Immutability**
   - Measurement data cannot be edited after creation
   - Only workbook metadata (title, sample name) can be modified

### Lab Admin Dashboard

#### Core Features
1. **Researcher Management**
   - Card grid of all researchers in lab
   - Search researchers by name/username
   - View researcher profile with workbooks
   - Activity status indicators (Active/Inactive)

2. **Statistics Tab**
   - Lab-level statistics:
     - Total researchers
     - Total workbooks
     - Total measurements
     - Instrument usage count
   - Recent activity feed:
     - Filterable by time range (7 days, 30 days, all time)
     - Shows workbook/measurement actions
     - Displays researcher, action, time, details

3. **Researcher Profile View**
   - Read-only view of researcher's workbooks
   - Search and filter capabilities
   - Open workbooks for review

### Super Admin Dashboard

#### Core Features
1. **Statistics Dashboard**
   - System-wide KPIs:
     - Total users, researchers, labs
     - Total workbooks, measurements
     - Instrument usage (30 days)
   - Instrument usage logs table (most recent first)

2. **Labs Management**
   - List of all labs
   - Create new lab
   - Open lab profile (view admins, researchers)

3. **Users Management**
   - List of all users
   - Create new user (with auto-generated password)
   - Edit user (role, lab, language, status)
   - Reset user password

4. **Lab Profile Window**
   - Lab details and metadata
   - Admins tab: List lab admins, add/remove
   - Researchers tab: List researchers, add/remove

5. **Audit Logs**
   - Complete system audit trail
   - Filterable by user, action, time

---

## Internationalization (i18n)

### Architecture

- **Translation Manager:** Singleton pattern with session-aware language detection
- **Translation Files:** JSON format with nested structure
- **Supported Languages:** English (en), Japanese (ja)
- **Language Preference:** Stored per-user in database, applied on login

### Translation Key Structure

```json
{
  "dashboard": {
    "welcome": "Welcome",
    "logout": "Logout",
    "researcher": "Researcher"
  },
  "researcher": {
    "search_workbooks": "Search workbooks:",
    "create_workbook": "Create Workbook"
  }
}
```

### Usage Pattern

```python
from src.i18n import tr

# Simple translation
label.setText(tr("dashboard.welcome"))

# With fallback
button.setText(tr("button.save", "Save"))
```

### Translation Scope

- **Translated:** Static UI elements (labels, buttons, messages, table headers)
- **Not Translated:** Dynamic content (user-entered data, measurement values, workbook titles)

### Language Loading Flow

1. User logs in → `SessionManager.login(user)`
2. Session loads `user.preferred_language` → `CurrentSession.set_user()`
3. Translation manager reads session language → `TranslationManager.get_current_language()`
4. UI elements refresh → `load_data()` → `_refresh_translated_ui()`
5. All `tr()` calls return translated text

---

## Services Layer

### WorkbookService

**Location:** `src/services/workbook_service.py`

**Methods:**
- `create_workbook(db, user, title, sample_name, ...)` - Create new workbook
- `get_workbook(db, workbook_id, user)` - Get workbook with access control
- `get_user_workbooks(db, user)` - Get all workbooks for user (role-aware)
- `update_workbook(db, workbook_id, user, **kwargs)` - Update metadata only
- `delete_workbook(db, workbook_id, user)` - Soft delete workbook

**Access Control:** Enforced at service level, checks user permissions before operations

### MeasurementService

**Location:** `src/services/measurement_service.py`

**Methods:**
- `create_measurement(db, workbook_id, measurement_type, raw_data, ...)` - Create measurement
- `get_measurements(db, workbook_id, user)` - Get measurements with access control

**Data Immutability:** Measurements are append-only; no update/delete methods

### UserService

**Location:** `src/services/user_service.py`

**Methods:**
- `create_user(db, creator, username, email, ...)` - Create user (super admin only)
- `update_user(db, user_id, updater, **kwargs)` - Update user (super admin only)
- `delete_user(db, user_id, deleter)` - Soft delete user (super admin only)
- `reset_password(db, user_id, new_password, admin)` - Reset password (super admin only)

**Password Generation:** Auto-generates unique 8-16 character alphanumeric passwords

### StatisticsService

**Location:** `src/services/statistics_service.py`

**Methods:**
- `get_researcher_statistics(db, researcher_id, start_date, end_date)` - Researcher stats
- `get_lab_statistics(db, lab_id, start_date, end_date)` - Lab-level aggregation
- `get_system_statistics(db)` - System-wide statistics
- `get_lab_activity_logs(db, lab_id, since, limit)` - Lab activity feed
- `get_instrument_usage_logs(db, limit)` - System-wide instrument logs

---

## User Interface Design

### Design Principles

1. **Minimal & Clean:** Industry-standard professional appearance
2. **University Branding:** Shizuoka University color scheme
3. **Card-Based Layout:** Modern card grid for workbooks/researchers
4. **Responsive Grid:** Dynamic card layout based on window size
5. **Consistent Navigation:** Role-appropriate dashboards with clear hierarchy

### Color Scheme

- **Primary Blue:** `#0078d4` (Buttons, links, highlights)
- **Success Green:** `#28a745` (Lab admin theme)
- **Info Teal:** `#17a2b8` (Researcher theme)
- **Danger Red:** `#dc3545` (Super admin theme, logout)
- **Neutral Gray:** `#d0d7de` (Borders, dividers)
- **Background:** `#f4f5fb` (Card container background)

### UI Components

#### Login Window
- Centered card layout
- University logo (top)
- Application title and subtitle
- Username/password fields
- Login button
- Account creation notice

#### Researcher Dashboard
- Header: Welcome message, role badge, logout
- Toolbar: Search input, refresh button
- Card Grid: "New Workbook" card + workbook cards
- Workbook Cards:
  - Editable title (inline)
  - Sample name, dates
  - Overflow menu (three dots) for delete
  - "Open Workbook" button

#### Lab Admin Dashboard
- Tabbed interface:
  - **Researchers Tab:** Card grid of researchers
  - **Statistics Tab:** Lab stats + activity feed
- Researcher Cards:
  - Name, username
  - Workbook count, measurements, instrument uses
  - Activity status badge
  - "View Workbooks" button

#### Super Admin Dashboard
- Tabbed interface:
  - **Statistics Dashboard:** System stats + instrument logs
  - **Labs Management:** Lab list with actions
  - **Users Management:** User list with actions
  - **Audit Logs:** Complete audit trail

### Workbook Window

- **Layout:** Full-screen maximized window
- **Tabs:** Bottom-aligned (Excel-style)
  - Tab 1: Seebeck Measurement
  - Tab 2: Electrical Resistivity
  - Tab 3: Thermal Conductivity
- **Content:** Measurement data tables (read-only)

---

## Configuration Management

### Configuration File

**Location:** `config/config.ini`

### Sections

#### [database]
```ini
db_type = postgresql  # or 'sqlite'
host = localhost
port = 5432
database = te_measurements
username = te_user
password = your_password
```

#### [storage]
```ini
data_directory = ./data
backup_directory = ./backups
```

#### [application]
```ini
app_name = TE Measurements
app_version = 1.0.0
debug = False
```

#### [security]
```ini
max_login_attempts = 5
lockout_duration_minutes = 15
session_timeout_minutes = 480
```

#### [instruments]
```ini
keithley_port = COM3
keithley_baudrate = 9600
```

### Environment-Specific Configuration

- **Development:** Use SQLite for quick setup
- **Production:** Use PostgreSQL for scalability
- **Configuration Loading:** `src/utils/config_loader.py`

---

## Deployment

### On-Premises Deployment

#### Hardware Requirements
- **CPU:** Dedicated workstation connected to Keithley measurement setup
- **Storage:** External hard disk for data storage
- **Network:** Local network access (if multi-user)

#### Deployment Steps

1. **Database Setup**
   ```bash
   # PostgreSQL setup (see PGADMIN_SETUP.md)
   # Create database and user
   # Run migrations: python scripts/init_db.py
   ```

2. **Application Installation**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd TE_Measurements
   
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux
   venv\Scripts\activate     # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Configuration**
   ```bash
   # Edit config/config.ini
   # Set database credentials
   # Configure instrument ports
   ```

4. **Initial Setup**
   ```bash
   # Create super admin
   python scripts/create_super_admin.py
   
   # (Optional) Seed dummy labs
   python scripts/seed_dummy_labs.py
   ```

5. **Run Application**
   ```bash
   python main.py
   ```

### Deployment Architecture

```
┌─────────────────────────────────────┐
│   Dedicated Workstation             │
│                                     │
│  ┌──────────────┐  ┌─────────────┐ │
│  │ TE           │  │ PostgreSQL  │ │
│  │ Measurements │◄─┤ Database    │ │
│  │ Application  │  │             │ │
│  └──────┬───────┘  └─────────────┘ │
│         │                          │
│         │ USB/Serial               │
│         ▼                          │
│  ┌──────────────┐                  │
│  │   Keithley   │                  │
│  │  Instrument  │                  │
│  └──────────────┘                  │
│                                     │
│  ┌──────────────┐                  │
│  │   External   │                  │
│  │  Hard Disk   │                  │
│  │  (Data)      │                  │
│  └──────────────┘                  │
└─────────────────────────────────────┘
```

---

## Development Setup

### Prerequisites

- Python 3.8+
- PostgreSQL 12+ (or SQLite 3.30+)
- Git
- Virtual environment tool (venv)

### Setup Instructions

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd TE_Measurements
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Database**
   - Edit `config/config.ini`
   - Set database connection details

5. **Initialize Database**
   ```bash
   python scripts/init_db.py
   ```

6. **Create Super Admin**
   ```bash
   python scripts/create_super_admin.py
   ```

7. **Run Application**
   ```bash
   python main.py
   ```

### Project Structure

```
TE_Measurements/
├── config/
│   └── config.ini              # Application configuration
├── src/
│   ├── auth/                   # Authentication & authorization
│   │   ├── auth_manager.py
│   │   └── session.py
│   ├── database.py             # Database connection & setup
│   ├── gui/                    # User interface components
│   │   ├── base_dashboard.py
│   │   ├── login_window.py
│   │   ├── researcher_dashboard.py
│   │   ├── lab_admin_dashboard.py
│   │   ├── super_admin_dashboard.py
│   │   ├── workbook_window.py
│   │   └── dialogs/
│   ├── i18n/                   # Internationalization
│   │   ├── __init__.py
│   │   └── translations/
│   ├── instruments/            # Instrument integration
│   ├── models/                 # Database models
│   ├── services/               # Business logic
│   └── utils/                  # Utility functions
├── scripts/                    # Setup & utility scripts
│   ├── init_db.py
│   ├── create_super_admin.py
│   └── create_user.py
├── assets/                     # Static assets (logos, etc.)
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
└── README.md                   # Project overview
```

---

## Security Considerations

### Password Security
- ✅ Bcrypt hashing with automatic salt
- ✅ Minimum 8 characters enforced
- ✅ Unique password generation (prevents collisions)
- ✅ No password storage in plain text

### Access Control
- ✅ Role-based access control (RBAC)
- ✅ Multi-tenant data isolation (lab-based)
- ✅ Service-level permission checks
- ✅ Immutable measurement data

### Session Security
- ✅ In-memory session management
- ✅ Automatic session cleanup on logout
- ✅ Account lockout after failed attempts
- ✅ Last login tracking

### Audit Logging
- ✅ Comprehensive audit trail
- ✅ User action tracking
- ✅ IP address and user agent logging
- ✅ Timestamp for all actions

### Data Protection
- ✅ Soft delete (data preservation)
- ✅ Foreign key constraints
- ✅ Transaction management (rollback on errors)
- ✅ Input validation

---

## Future Enhancements

### Planned Features

1. **Instrument Integration**
   - Direct Keithley instrument connection
   - Real-time measurement capture
   - Automated data parsing

2. **Advanced Analytics**
   - Data visualization (charts, graphs)
   - Export functionality (CSV, Excel, PDF)
   - Statistical analysis tools

3. **Enhanced Comments**
   - Threaded comments
   - Comment attachments
   - Email notifications

4. **Multi-Lab Permissions**
   - UI for managing multi-lab access
   - Cross-lab workbook sharing (optional)

5. **Backup & Recovery**
   - Automated database backups
   - Data export/import tools
   - Point-in-time recovery

6. **Performance Optimization**
   - Database query optimization
   - Caching layer
   - Lazy loading for large datasets

---

## Appendix

### A. Database Migration Scripts

See `scripts/init_db.py` for database initialization.

### B. User Creation Scripts

- `scripts/create_super_admin.py` - Create initial super admin
- `scripts/create_user.py` - Create users of any role

### C. Configuration Examples

See `config/config.ini` for complete configuration template.

### D. API Reference

All service methods are documented in their respective files:
- `src/services/workbook_service.py`
- `src/services/measurement_service.py`
- `src/services/user_service.py`
- `src/services/statistics_service.py`

### E. Translation Keys Reference

See `src/i18n/translations/en.json` for complete list of translation keys.

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | Dec 2024 | Development Team | Initial technical documentation |

---

**End of Document**

