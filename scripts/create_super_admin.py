#!/usr/bin/env python3
"""
Create initial super admin user
"""

import sys
import os
import getpass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_database, get_db
from src.models import User, UserRole


def main():
    """Create super admin user"""
    print("Creating Super Admin User")
    print("=" * 40)
    
    # Get user input
    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty!")
        sys.exit(1)
    
    email = input("Email: ").strip()
    if not email:
        print("Email cannot be empty!")
        sys.exit(1)
    
    full_name = input("Full Name: ").strip()
    if not full_name:
        print("Full name cannot be empty!")
        sys.exit(1)
    
    password = getpass.getpass("Password: ")
    if len(password) < 8:
        print("Password must be at least 8 characters!")
        sys.exit(1)
    
    password_confirm = getpass.getpass("Confirm Password: ")
    if password != password_confirm:
        print("Passwords do not match!")
        sys.exit(1)
    
    # Initialize database
    try:
        init_database()
        db = next(get_db())
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.username == username).first()
        if existing_user:
            print(f"User '{username}' already exists!")
            sys.exit(1)
        
        # Create super admin
        super_admin = User(
            username=username,
            email=email,
            full_name=full_name,
            role=UserRole.SUPER_ADMIN,
            is_active=True
        )
        super_admin.set_password(password)
        
        db.add(super_admin)
        db.commit()
        
        print(f"\nSuper admin '{username}' created successfully!")
        
    except Exception as e:
        print(f"Error creating super admin: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()

