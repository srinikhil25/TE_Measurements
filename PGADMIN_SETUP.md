# pgAdmin Setup Guide for TE Measurements

## Step 1: Install PostgreSQL and pgAdmin

### Option A: Install PostgreSQL (includes pgAdmin)
1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. During installation, make sure to:
   - Install pgAdmin 4 (it's included in the installer)
   - Remember the PostgreSQL superuser password (you'll need it)
   - Note the port (default is 5432)

### Option B: Install pgAdmin separately
1. Download pgAdmin 4 from: https://www.pgadmin.org/download/
2. Install it
3. Make sure PostgreSQL server is already installed and running

## Step 2: Start PostgreSQL Service

### Windows:
1. Open **Services** (Win + R, type `services.msc`)
2. Find **postgresql-x64-XX** (where XX is version number)
3. Right-click → **Start** (if not already running)
4. Set it to **Automatic** startup (Right-click → Properties → Startup type: Automatic)

### Verify PostgreSQL is running:
```powershell
# Check if PostgreSQL is listening on port 5432
netstat -an | findstr 5432
```

## Step 3: Launch pgAdmin

1. Open **pgAdmin 4** from Start Menu
2. You'll be prompted for a master password (first time only) - set a secure password
3. pgAdmin will open in your web browser (usually http://127.0.0.1:xxxxx)

## Step 4: Connect to PostgreSQL Server in pgAdmin

1. In pgAdmin, you'll see **Servers** in the left panel
2. Expand **Servers** → **PostgreSQL XX** (where XX is version)
3. If you see a lock icon, right-click → **Connect Server**
4. Enter the PostgreSQL superuser password (the one you set during installation)
5. Click **Save** if you want to save the password

## Step 5: Create Database for TE Measurements

1. Right-click on **Databases** → **Create** → **Database...**
2. Fill in the form:
   - **Database name**: `te_measurements`
   - **Owner**: Leave as default (postgres) or select your user
   - **Encoding**: UTF8 (default)
   - Click **Save**

## Step 6: Create Database User

1. Expand **te_measurements** database
2. Expand **Login/Group Roles**
3. Right-click → **Create** → **Login/Group Role...**
4. Fill in the form:
   - **General** tab:
     - **Name**: `te_user`
   - **Definition** tab:
     - **Password**: Enter a secure password (remember this!)
     - **Password expiration**: Uncheck if you don't want it to expire
   - **Privileges** tab:
     - **Can login?**: Yes
     - **Create databases?**: No (unless needed)
     - **Create roles?**: No
   - Click **Save**

## Step 7: Grant Permissions to User

1. Right-click on **te_measurements** database → **Properties**
2. Go to **Security** tab
3. Click **+** to add a new privilege
4. Select **te_user** from dropdown
5. Check **ALL** privileges (or at least: CONNECT, CREATE, TEMPORARY)
6. Click **Save**

## Step 8: Update Application Configuration

Edit `config/config.ini`:

```ini
[database]
db_type = postgresql
host = localhost
port = 5432
database = te_measurements
username = te_user
password = YOUR_PASSWORD_HERE  # The password you set in Step 6
```

**Important**: Replace `YOUR_PASSWORD_HERE` with the actual password you set for `te_user`.

## Step 9: Initialize Database Tables

Run the initialization script:

```powershell
# Make sure you're in the project directory and venv is activated
python scripts/init_db.py
```

This will create all the necessary tables in your database.

## Step 10: Verify in pgAdmin

1. In pgAdmin, expand **te_measurements** → **Schemas** → **public** → **Tables**
2. You should see these tables:
   - `users`
   - `labs`
   - `workbooks`
   - `measurements`
   - `comments`
   - `audit_logs`
   - `user_lab_permissions`

## Step 11: Create Super Admin User

```powershell
python scripts/create_super_admin.py
```

Follow the prompts to create your first super admin account.

## Troubleshooting

### Cannot connect to PostgreSQL
- Check if PostgreSQL service is running (Step 2)
- Verify port 5432 is not blocked by firewall
- Check PostgreSQL is listening: `netstat -an | findstr 5433`

### Authentication failed
- Verify username and password in `config/config.ini`
- Check if user has login privileges in pgAdmin
- Try connecting with pgAdmin first to verify credentials

### Permission denied errors
- Make sure `te_user` has proper permissions on `te_measurements` database
- Grant ALL privileges in database properties (Step 7)

### Database doesn't exist
- Create it manually in pgAdmin (Step 5)
- Or run: `createdb -U postgres te_measurements` in command line

### Tables not created
- Run `python scripts/init_db.py` again
- Check for errors in the output
- Verify database connection in `config/config.ini`

## Using pgAdmin for Database Management

### Viewing Data
- Expand **Tables** → Right-click table → **View/Edit Data** → **All Rows**

### Running Queries
- Click **Tools** → **Query Tool**
- Write SQL queries
- Click **Execute** (F5)

### Backup Database
- Right-click **te_measurements** → **Backup...**
- Choose filename and location
- Click **Backup**

### Restore Database
- Right-click **te_measurements** → **Restore...**
- Select backup file
- Click **Restore**

## Security Notes

1. **Never commit passwords** - Keep `config/config.ini` out of version control (already in `.gitignore`)
2. **Use strong passwords** - Especially for PostgreSQL superuser
3. **Limit permissions** - `te_user` only needs access to `te_measurements` database
4. **Regular backups** - Use pgAdmin to backup your database regularly

## Next Steps

Once setup is complete:
1. ✅ Database created
2. ✅ User created with permissions
3. ✅ Tables initialized
4. ✅ Super admin created
5. ✅ Application configured

You can now run the application:
```powershell
python main.py
```

And manage your database through pgAdmin's friendly GUI interface!

