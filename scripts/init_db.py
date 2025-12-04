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
from app.core.security import get_password_hash

def init_db():
    """Create all tables and default admin user."""
    # Create all tables
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")
    
    # Create default admin user
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin = db.query(User).filter(User.username == "admin").first()
        if admin:
            print("Admin user already exists. Skipping creation.")
            return
        
        # Create default admin
        admin_user = User(
            username="admin",
            email="admin@seebeck.local",
            hashed_password=get_password_hash("admin"),
            full_name="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            created_by=None
        )
        db.add(admin_user)
        db.commit()
        print("Default admin user created successfully!")
        print("Username: admin")
        print("Password: admin")
        print("⚠️  IMPORTANT: Change the default password in production!")
    except Exception as e:
        db.rollback()
        print(f"Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()

