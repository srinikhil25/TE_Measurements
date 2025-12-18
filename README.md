# TE Measurements - Desktop Application

A professional desktop application for researchers to measure Seebeck measurements, electrical resistivity, and thermal conductivity with strict access control and multi-tenant lab management.

## Features

- **Multi-tenant Lab Management**: Strict isolation between labs and researchers
- **Role-Based Access Control**: Three roles (Researcher, Lab Admin, Super Admin)
- **Workbook System**: Organize experiments with multiple measurement types
- **Instrument Integration**: Direct connection to Keithley measurement setup
- **Data Integrity**: Immutable instrument data with audit trails
- **Statistics & Reporting**: Comprehensive analytics for all user roles

## Architecture

- **GUI Framework**: PyQt6 (cross-platform)
- **Backend**: Python 3.9+
- **Database**: PostgreSQL (with SQLite fallback)
- **ORM**: SQLAlchemy
- **Platforms**: Windows & Linux

## Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL (or SQLite for single-user setup)
- Qt6 libraries

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure database connection in `config/config.ini`

3. Run database migrations:
```bash
python scripts/init_db.py
```

4. Create initial super admin:
```bash
python scripts/create_super_admin.py
```

5. Launch application:
```bash
python main.py
```

## Project Structure

```
TE_Measurements/
├── main.py                 # Application entry point
├── config/                 # Configuration files
├── src/
│   ├── gui/               # PyQt6 GUI components
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   ├── auth/              # Authentication & authorization
│   ├── instruments/       # Instrument connection modules
│   └── utils/             # Utility functions
├── data/                  # Raw measurement data storage
├── scripts/               # Database and setup scripts
└── tests/                 # Unit tests
```

## User Roles

### Researcher
- Create and manage workbooks
- View own measurements (read-only instrument data)
- Belongs to one lab by default
- **Cannot create accounts** - accounts are created by super admins

### Lab Admin
- View all researchers' work in their lab
- Comment on researchers' work
- View statistics and analytics
- Cannot edit or delete data
- **Cannot create accounts** - accounts are created by super admins

### Super Admin
- Manage labs, lab admins, and researchers
- **Create user accounts** (only role that can create accounts)
- View system-wide statistics dashboard
- Access audit logs
- Full system administration

## Authentication

**Important**: User accounts can only be created by super administrators. Researchers and lab admins cannot create their own accounts. When a super admin creates an account, they will provide the username and password to the user.

## License

Proprietary - For internal research use only

