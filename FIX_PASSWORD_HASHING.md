# Fix Password Hashing Issue

## Problem
bcrypt 5.0.0 is incompatible with passlib, causing password hashing to fail.

## Solution: Switch to Argon2

Argon2 is more secure than bcrypt and doesn't have compatibility issues. Run these commands:

```powershell
pip uninstall bcrypt -y
pip install "passlib[argon2]"
```

Then run the database initialization:
```powershell
python scripts/init_db.py
```

## What Changed
- Switched from bcrypt to argon2 in `requirements.txt`
- Updated `app/core/security.py` to use argon2
- Argon2 has no password length limit (unlike bcrypt's 72-byte limit)

## Benefits of Argon2
- More secure than bcrypt
- No password length limitations
- Better resistance to GPU-based attacks
- No compatibility issues with newer Python versions

