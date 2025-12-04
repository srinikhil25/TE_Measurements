# Fixing Bcrypt Compatibility Issue

## Problem
The bcrypt library version is incompatible with passlib, causing password hashing to fail.

## Solution

Run these commands in your terminal (with venv activated):

```powershell
pip uninstall bcrypt -y
pip install bcrypt>=4.0.0
pip install --upgrade passlib[bcrypt]
```

Then run the database initialization again:
```powershell
python scripts/init_db.py
```

## Alternative: Use a different password hasher

If bcrypt continues to cause issues, we can switch to argon2 (more secure, no 72-byte limit):

```powershell
pip install passlib[argon2]
```

Then update `app/core/security.py` to use:
```python
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
```

