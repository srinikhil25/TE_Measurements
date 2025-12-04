# Seebeck Measurement System

A professional, industry-standard desktop application for Seebeck coefficient measurements with secure authentication and admin-controlled user management.

## Features

- 🔐 **Secure Authentication** - JWT-based authentication system
- 👥 **Admin-Controlled Users** - Only admins can create and manage user accounts
- 📚 **Workbook/Sample Management** - Organize measurements by sample
- 📊 **Real-time Measurements** - Live data visualization and monitoring
- 🔌 **Instrument Control** - Direct control of Keithley 2182A, 2700, and PK160 instruments
- 📈 **Data Visualization** - Real-time graphs and charts
- 💾 **Data Export** - Export measurements to CSV and Excel formats
- 🖥️ **Cross-platform** - Works on Windows, Linux, and macOS

## Architecture

This application follows industry best practices with:

- **Backend**: FastAPI with SQLAlchemy ORM
- **Frontend**: Flet desktop application
- **Database**: SQLite (development) / PostgreSQL (production)
- **Authentication**: JWT tokens with role-based access control
- **Security**: Password hashing, secure token storage
         
See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed architecture documentation.

## Prerequisites

- Python 3.14.1
- PyVISA backend (NI-VISA, pyvisa-py, or similar)
- GPIB interface for Keithley instruments

## Installation

1. **Clone or navigate to this directory:**
   ```bash
   cd TE_Measurement
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   
   # On Windows:
   .\venv\Scripts\activate.bat
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   # Copy the example .env file
   copy .env.example .env
   
   # Edit .env and set your SECRET_KEY (use a strong random key in production)
   ```

5. **Initialize database:**
   ```bash
   python scripts/init_db.py
   ```
   
   This will:
   - Create all database tables
   - Create default admin user:
     - Username: `admin`
     - Password: `admin`
     - ⚠️ **IMPORTANT**: Change this password in production!

## Running the Application

### Step 1: Start the Backend API Server

Open a terminal and run:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

### Step 2: Start the Desktop Application

Open another terminal and run:
```bash
python desktop/main.py
```

## Default Login Credentials

- **Username**: `admin`
- **Password**: `admin`

⚠️ **Change these credentials in production!**

## User Roles

- **Admin**: Full access, can manage users and view all data
- **Researcher**: Can perform measurements and view only their own data

## Project Structure

```
TE_Measurement/
├── app/              # FastAPI backend
│   ├── api/         # API routes
│   ├── core/        # Core functionality (config, security)
│   ├── models/      # Database models
│   └── schemas/     # Pydantic schemas
├── desktop/         # Flet desktop application
│   ├── ui/          # UI components
│   └── api_client.py # API client
├── scripts/         # Utility scripts
└── migrations/      # Database migrations (Alembic)
```

## Development

### Running Tests
```bash
pytest
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

## Instrument Connections

See [INSTRUMENT_CONNECTIONS.md](INSTRUMENT_CONNECTIONS.md) for detailed information about Keithley instrument connections and GPIB addresses.

## License

For internal use - Ikeda-Hamasaki Laboratory

## Support

For issues or questions, please contact the development team.
