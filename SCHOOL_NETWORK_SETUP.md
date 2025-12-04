# School Network Setup Guide

## Port Restrictions

School networks often block certain ports. We're using **port 8080** instead of 8000, and binding to **127.0.0.1** (localhost only) to avoid network restrictions.

## Starting the Backend

### Option 1: PowerShell Script (Recommended)
```powershell
.\start_backend.ps1
```

### Option 2: Manual Command
```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

### Option 3: Batch File
Double-click `start_backend.bat` or run:
```powershell
.\start_backend.bat
```

## Alternative Ports

If port 8080 is also blocked, try these ports:
- 5000: `--port 5000`
- 3000: `--port 3000`
- 8888: `--port 8888`

Just remember to update `desktop/api_client.py` with the new port:
```python
base_url: str = "http://localhost:YOUR_PORT"
```

## Why 127.0.0.1 instead of 0.0.0.0?

- `127.0.0.1` (localhost) - Only accessible from your computer (safer for school networks)
- `0.0.0.0` - Accessible from network (may be blocked/restricted)

## Testing

After starting the backend, test it:
1. Open browser: http://localhost:8080/health
2. Should see: `{"status": "healthy"}`
3. API docs: http://localhost:8080/docs

