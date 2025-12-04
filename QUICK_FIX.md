# Quick Fix Guide

## Issue 1: Missing email-validator

Run:
```powershell
pip install "pydantic[email]" email-validator
```

## Issue 2: Module import errors

The desktop app needs the project root in Python path. I've fixed the imports in:
- `desktop/main.py`
- `desktop/ui/login.py`

## After fixing, restart:

1. **Backend:**
   ```powershell
   .\start_backend.ps1
   ```

2. **Desktop App:**
   ```powershell
   python desktop/main.py
   ```

