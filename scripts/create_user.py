#!/usr/bin/env python3
"""
Create a user of any role (researcher, lab_admin, super_admin).

Usage:
    python scripts/create_user.py

This is mainly for development / initial setup. In production, super
admins will manage users from the UI.
"""

import sys
import os
import getpass

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_database, get_db  # type: ignore[import]
from src.models import User, UserRole, Lab  # type: ignore[import]


def select_role() -> UserRole:
    print("Select role:")
    print("  1) Researcher")
    print("  2) Lab Admin")
    print("  3) Super Admin")
    choice = input("Role [1-3]: ").strip()
    mapping = {"1": UserRole.RESEARCHER, "2": UserRole.LAB_ADMIN, "3": UserRole.SUPER_ADMIN}
    if choice not in mapping:
        print("Invalid choice. Please run again.")
        sys.exit(1)
    return mapping[choice]


def select_lab(db, role: UserRole) -> int | None:
    """Prompt for lab_id when needed (researcher/lab_admin)."""
    if role == UserRole.SUPER_ADMIN:
        return None

    labs = db.query(Lab).filter(Lab.is_active == True).order_by(Lab.id.asc()).all()  # noqa: E712
    if not labs:
        print("No labs found. Please create a lab first (via super admin) before creating this user.")
        sys.exit(1)

    print("\nAvailable labs:")
    for lab in labs:
        print(f"  {lab.id}) {lab.name}")

    while True:
        lab_input = input("Lab ID for this user: ").strip()
        if not lab_input.isdigit():
            print("Please enter a numeric lab ID.")
            continue
        lab_id = int(lab_input)
        if any(l.id == lab_id for l in labs):
            return lab_id
        print("Invalid lab ID. Please choose from the list above.")


def main():
    print("Create User")
    print("===========")

    # Get basic info
    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty.")
        sys.exit(1)

    email = input("Email: ").strip()
    if not email:
        print("Email cannot be empty.")
        sys.exit(1)

    full_name = input("Full Name: ").strip()
    if not full_name:
        print("Full name cannot be empty.")
        sys.exit(1)

    role = select_role()

    password = getpass.getpass("Password: ")
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)

    confirm = getpass.getpass("Confirm Password: ")
    if password != confirm:
        print("Passwords do not match.")
        sys.exit(1)

    # Initialize DB
    try:
        init_database()
        db = next(get_db())

        # Check username/email uniqueness
        if db.query(User).filter(User.username == username).first():
            print(f"Username '{username}' already exists.")
            sys.exit(1)
        if db.query(User).filter(User.email == email).first():
            print(f"Email '{email}' is already registered.")
            sys.exit(1)

        lab_id = select_lab(db, role)

        user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            lab_id=lab_id if role != UserRole.SUPER_ADMIN else None,
            is_active=True,
        )
        user.set_password(password)

        db.add(user)
        db.commit()

        print("\nUser created successfully!")
        print(f"  Username : {username}")
        print(f"  Email    : {email}")
        print(f"  Full Name: {full_name}")
        print(f"  Role     : {role.value}")
        if lab_id is not None:
            print(f"  Lab ID   : {lab_id}")

    except Exception as e:
        print(f"Error creating user: {e}")
        sys.exit(1)
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()


