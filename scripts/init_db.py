"""
Initialize database and create default admin user.
Run this script once to set up the database.
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.database import Base, engine, SessionLocal
from app.models.user import User, UserRole
from app.models.lab import Lab
from app.core.security import get_password_hash

def init_db():
    """Create all tables and default lab/users."""
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    
    # Create default lab and users
    db = SessionLocal()
    try:
        # Check if any labs exist
        existing_lab = db.query(Lab).first()
        if existing_lab:
            print("Database already initialized. Skipping creation.")
            return

        # Create default labs
        default_lab = Lab(
            lab_name="Ikeda-Hamasaki Laboratory",
            lab_code="1111",
            lab_description="IAdvanced Device Research Laboratory",
        )
        lab_b = Lab(
            lab_name="Thermoelectric Materials Lab",
            lab_code="2222",
            lab_description="Thermoelectric materials and device development.",
        )
        lab_c = Lab(
            lab_name="Nanostructure Physics Lab",
            lab_code="3333",
            lab_description="Nanostructured thermoelectric physics laboratory.",
        )
        lab_d = Lab(
            lab_name="Energy Conversion Lab",
            lab_code="4444",
            lab_description="Energy conversion and transport measurements lab.",
        )
        db.add_all([default_lab, lab_b, lab_c, lab_d])
        db.flush()  # assign lab_ids

        # Create super admin (no lab_id)
        super_admin = User(
            username="superadmin",
            email="superadmin@seebeck.local",
            hashed_password=get_password_hash("superadmin"),
            full_name="Super Administrator",
            role=UserRole.SUPER_ADMIN,
            is_active=True,
            lab_id=None,
            created_by=None,
        )
        db.add(super_admin)

        # Create lab admin for default lab
        lab_admin = User(
            username="labadmin",
            email="labadmin@seebeck.local",
            hashed_password=get_password_hash("labadmin"),
            full_name="Lab Administrator",
            role=UserRole.LAB_ADMIN,
            is_active=True,
            lab_id=default_lab.lab_id,
            created_by=super_admin.id,
        )
        db.add(lab_admin)

        # Create researcher for default lab
        researcher_user = User(
            username="researcher",
            email="researcher@seebeck.local",
            hashed_password=get_password_hash("researcher"),
            full_name="Test Researcher",
            role=UserRole.RESEARCHER,
            is_active=True,
            lab_id=default_lab.lab_id,
            created_by=lab_admin.id,
        )
        db.add(researcher_user)

        db.commit()
        print("Default labs and users created successfully!")
        print("\nLabs:")
        for lab in [default_lab, lab_b, lab_c, lab_d]:
            print(f"  lab_id: {lab.lab_id} | lab_name: {lab.lab_name} | lab_code: {lab.lab_code}")
        print("\nSuper Admin User:")
        print("  Username: superadmin")
        print("  Password: superadmin")
        print("\nLab Admin User:")
        print("  Username: labadmin")
        print("  Password: labadmin")
        print("\nResearcher User:")
        print("  Username: researcher")
        print("  Password: researcher")
        print("\n⚠️  IMPORTANT: Change the default passwords in production!")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()

