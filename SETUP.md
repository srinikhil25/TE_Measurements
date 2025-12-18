# TE Measurements - Setup Guide

## Prerequisites

### Windows
1. Python 3.9 or higher ([Download](https://www.python.org/downloads/))
2. PostgreSQL 12+ (optional, SQLite can be used for single-user setup)
3. Qt6 libraries (installed automatically with PyQt6)

### Linux
1. Python 3.9 or higher
2. PostgreSQL 12+ (optional)
3. Qt6 development libraries:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install python3-pyqt6 python3-pyqt6-dev
   
   # Fedora/RHEL
   sudo dnf install python3-qt6
   ```

## Installation Steps

### 1. Clone/Extract Project
```bash
cd TE_Measurements
```

### 2. Create Virtual Environment (Recommended)
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Database

#### Option A: PostgreSQL (Recommended for Multi-User)
1. Install and start PostgreSQL
2. Create database:
   ```sql
   CREATE DATABASE te_measurements;
   CREATE USER te_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE te_measurements TO te_user;
   ```
3. Edit `config/config.ini`:
   ```ini
   [database]
   db_type = postgresql
   host = localhost
   port = 5432
   database = te_measurements
   username = te_user
   password = your_password
   ```

#### Option B: SQLite (Single-User Setup)
Edit `config/config.ini`:
```ini
[database]
db_type = sqlite
sqlite_path = data/te_measurements.db
```

### 5. Configure Storage Paths
Edit `config/config.ini`:
```ini
[storage]
# Path to external harddisk for raw data
raw_data_path = D:/TE_Measurements_Data
backup_path = D:/TE_Measurements_Backup
```

### 6. Initialize Database
```bash
python scripts/init_db.py
```

### 7. Create Super Admin
```bash
python scripts/create_super_admin.py
```
Follow the prompts to create the first super admin user.

### 8. Configure Instrument Connection
Edit `src/instruments/keithley_connection.py` and integrate your existing Keithley connection code.

### 9. Run Application
```bash
python main.py
```

## First-Time Setup Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Database configured (PostgreSQL or SQLite)
- [ ] Storage paths configured in `config/config.ini`
- [ ] Database initialized (`python scripts/init_db.py`)
- [ ] Super admin created (`python scripts/create_super_admin.py`)
- [ ] Instrument connection code integrated
- [ ] Application runs successfully

## Troubleshooting

### Database Connection Errors
- Verify PostgreSQL is running (if using PostgreSQL)
- Check database credentials in `config/config.ini`
- Ensure database and user exist

### PyQt6 Import Errors
- On Linux, install system Qt6 libraries (see Prerequisites)
- Verify virtual environment is activated
- Reinstall: `pip install --force-reinstall PyQt6`

### Permission Errors (Storage Paths)
- Ensure external harddisk is mounted and accessible
- Check write permissions on storage directories
- Create directories manually if needed

### Instrument Connection Issues
- Verify instrument is powered on and connected
- Check instrument address in `config/config.ini`
- Review instrument connection code in `src/instruments/keithley_connection.py`

## Next Steps

1. **Login as Super Admin**: Use the credentials created in step 7
2. **Create Labs**: Add labs through the Super Admin dashboard
3. **Create Lab Admins**: Assign lab administrators
4. **Create Researchers**: Add researchers to labs
5. **Test Instrument Connection**: Verify Keithley connection works
6. **Create Test Workbook**: Create a workbook and take a test measurement

## Development Notes

- Database models are in `src/models/`
- GUI components are in `src/gui/`
- Business logic is in `src/services/`
- Instrument integration is in `src/instruments/`
- Configuration is in `config/config.ini`

## Support

For issues or questions, contact the development team.

