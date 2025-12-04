# Testing Guide

## Step 1: Start the Backend API Server

Open a terminal (Terminal 1) and run:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Keep this terminal open!**

## Step 2: Test the API (Optional)

Open a browser and go to:
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

You can test the login endpoint in the API docs:
1. Go to `/api/auth/login`
2. Click "Try it out"
3. Enter:
   ```json
   {
     "username": "admin",
     "password": "admin"
   }
   ```
4. Click "Execute"
5. You should get a JWT token back

## Step 3: Start the Desktop Application

Open another terminal (Terminal 2) and run:

```powershell
python desktop/main.py
```

The login screen should appear with:
- Logo (science icon)
- User ID field (centered)
- Password field (centered)
- Login button

## Step 4: Test Login

1. Enter username: `admin`
2. Enter password: `admin`
3. Click "Login"

If successful, you should see "Login Successful!" message.

## Troubleshooting

### Backend won't start
- Make sure port 8000 is not in use
- Check if all dependencies are installed: `pip install -r requirements.txt`

### Desktop app can't connect
- Make sure backend is running first
- Check if backend is on `http://localhost:8000`
- Check firewall settings

### Login fails
- Verify admin user exists: Check `seebeck_measurement.db` file exists
- Try re-running: `python scripts/init_db.py`
- Check backend logs for errors

## Next Steps After Testing

Once login works, we'll build:
1. Dashboard screen (workbook list)
2. Workbook creation
3. Measurement panels (Seebeck, Electrical Conductivity, Resistance)

