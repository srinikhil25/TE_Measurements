# Seebeck Measurement System - Architecture Plan

## Overview
Industry-standard desktop application for Seebeck coefficient measurements with secure authentication and admin-controlled user management.

## Technology Stack

### Backend
- **Python 3.14.1**
- **FastAPI** - Modern, fast web framework for API
- **SQLAlchemy** - ORM for database management
- **SQLite/PostgreSQL** - Database (SQLite for development, PostgreSQL for production)
- **PyVISA** - Instrument communication
- **Pydantic** - Data validation
- **Passlib** - Password hashing (bcrypt)
- **python-jose** - JWT tokens for authentication

### Frontend
- **Flet** - Cross-platform desktop UI framework
- **Matplotlib** - Data visualization
- **Pandas** - Data manipulation

## Project Structure

```
TE_Measurement/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection & session
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py             # Dependencies (auth, db session)
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── users.py        # User management (admin only)
│   │   │   ├── measurements.py # Measurement endpoints
│   │   │   └── instruments.py  # Instrument control
│   │   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # Password hashing, JWT
│   │   ├── config.py            # Settings
│   │   └── instrument.py       # Instrument classes (extracted)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User SQLAlchemy model
│   │   ├── measurement.py     # Measurement data models
│   │   └── schemas.py          # Pydantic schemas
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py     # Authentication logic
│   │   ├── user_service.py    # User management
│   │   ├── measurement_service.py # Measurement logic
│   │   └── instrument_service.py  # Instrument control
│   │
│   └── utils/
│       ├── __init__.py
│       └── logger.py           # Logging configuration
│
├── desktop/
│   ├── __init__.py
│   ├── main.py                 # Flet desktop app entry
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── login.py            # Login screen
│   │   ├── dashboard.py        # Main dashboard
│   │   ├── measurement_panel.py # Measurement UI
│   │   └── admin_panel.py      # Admin user management
│   │
│   └── api_client.py           # API client for backend
│
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_measurements.py
│   └── test_instruments.py
│
├── migrations/                 # Alembic database migrations
├── requirements.txt
├── README.md
├── INSTRUMENT_CONNECTIONS.md
└── ARCHITECTURE.md

```

## Authentication System

### User Roles
1. **Admin** - Full access, can manage users
2. **Researcher** - Can perform measurements, view data

### Authentication Flow
1. User logs in with username/password
2. Backend validates credentials
3. JWT token issued with user role
4. Token stored securely in desktop app
5. All API requests include token in Authorization header
6. Backend validates token and checks permissions

### User Management
- **No self-registration** - Only admins can create users
- Admin panel for:
  - Create new users
  - Edit user details
  - Deactivate/activate users
  - Change user roles
  - Reset passwords

### Security Features
- Password hashing with bcrypt
- JWT tokens with expiration
- Role-based access control (RBAC)
- Secure token storage
- Session management

## Database Schema

### Users Table
```sql
- id (Primary Key)
- username (Unique)
- email (Unique)
- hashed_password
- full_name
- role (admin/researcher)
- is_active (boolean)
- created_at
- updated_at
- created_by (admin who created this user)
```

### Workbooks Table (Samples)
```sql
- id (Primary Key)
- name (workbook/sample name) - required
- description (optional)
- material_type (optional)
- sample_id_code (optional)
- date_received (optional)
- researcher_id (Foreign Key -> Users.id)
- created_at
- updated_at
- is_active (boolean)
```

### Measurements Table
```sql
- id (Primary Key)
- workbook_id (Foreign Key -> Workbooks.id)
- researcher_id (Foreign Key -> Users.id)
- measurement_type (seebeck/electrical_conductivity/resistance_conductivity)
- measurement_params (JSON - stores all measurement parameters)
- status (running/completed/failed)
- started_at
- completed_at
- data_file_path (path to stored measurement data - hybrid storage)
- created_at
```

### Measurement Data Table (or JSON storage)
```sql
- id (Primary Key)
- measurement_id (Foreign Key -> Measurements.id)
- timestamp
- temf_mv (float)
- temp1_c (float)
- temp2_c (float)
- delta_temp_c (float)
- current_value (float)
```

## Data Isolation

- **Researchers** can only access:
  - Their own workbooks/samples
  - Measurements within their workbooks
  - Cannot see other researchers' data

- **Admins** can:
  - Manage users (create, edit, deactivate)
  - View all workbooks and measurements (professor oversight)
  - Export system-wide data
  - Access all researcher data

## Workbook/Sample Structure

Each **Workbook** represents work on a different sample:
- A researcher can have multiple workbooks
- Each workbook contains multiple measurement sessions
- Measurements are organized by workbook for easy management
- Workbook metadata includes: name, description, material_type, sample_id_code, date_received
- **Strictly private** - each workbook belongs only to its creator
- Researchers can export data manually to share
- **Measurement Types**: Seebeck, Electrical Conductivity, Resistance Conductivity
- After creating workbook, user selects measurement type (each has its own template)

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login, returns JWT token
- `POST /api/auth/logout` - Logout (token invalidation)
- `POST /api/auth/refresh` - Refresh token

### Users (Admin only)
- `GET /api/users` - List all users
- `POST /api/users` - Create new user
- `GET /api/users/{id}` - Get user details
- `PUT /api/users/{id}` - Update user
- `DELETE /api/users/{id}` - Deactivate user
- `POST /api/users/{id}/reset-password` - Reset password

### Workbooks (Samples)
- `GET /api/workbooks` - List user's workbooks
- `POST /api/workbooks` - Create new workbook
- `GET /api/workbooks/{id}` - Get workbook details
- `PUT /api/workbooks/{id}` - Update workbook
- `DELETE /api/workbooks/{id}` - Delete workbook (soft delete)

### Measurements
- `POST /api/workbooks/{workbook_id}/measurements/start` - Start measurement session
- `POST /api/measurements/{id}/stop` - Stop measurement
- `GET /api/measurements/{id}/status` - Get session status
- `GET /api/measurements/{id}/data` - Get measurement data
- `GET /api/workbooks/{workbook_id}/measurements` - Get all measurements in workbook
- `POST /api/measurements/{id}/export` - Export single measurement data
- `POST /api/workbooks/{workbook_id}/export` - Export all measurements in workbook

### Instruments
- `POST /api/instruments/connect` - Connect to instruments
- `POST /api/instruments/disconnect` - Disconnect
- `GET /api/instruments/status` - Get instrument status

## Development Phases

### Phase 1: Foundation
- [ ] Project structure setup
- [ ] Database models and migrations
- [ ] Basic FastAPI setup
- [ ] Authentication system
- [ ] User management (admin)

### Phase 2: Core Features
- [ ] Instrument connection layer
- [ ] Measurement session management
- [ ] API endpoints for measurements
- [ ] Basic desktop UI (login, dashboard)

### Phase 3: UI Development
- [ ] Measurement panel UI
- [ ] Real-time data visualization
- [ ] Data export functionality
- [ ] Admin panel UI

### Phase 4: Testing & Polish
- [ ] Unit tests
- [ ] Integration tests
- [ ] Error handling
- [ ] Documentation
- [ ] Deployment guide

## Industry Standards Applied

1. **Separation of Concerns** - Clear separation between API, services, and UI
2. **Security** - Proper authentication, password hashing, JWT tokens
3. **Database** - ORM with migrations, proper schema design
4. **API Design** - RESTful endpoints, proper HTTP methods
5. **Error Handling** - Comprehensive error handling and logging
6. **Testing** - Unit and integration tests
7. **Documentation** - Code documentation and API docs
8. **Configuration** - Environment-based configuration
9. **Logging** - Structured logging
10. **Code Quality** - Type hints, linting, formatting

