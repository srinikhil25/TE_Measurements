#!/usr/bin/env python3
"""
Initialize database - Create all tables
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_database, create_tables, Base

# Import all models so SQLAlchemy registers them
from src.models import (
    User, UserRole,
    Lab,
    Workbook,
    Measurement, MeasurementType,
    Comment,
    AuditLog, AuditActionType
)
from src.models.associations import user_lab_permissions


def main():
    """Initialize database"""
    print("Initializing database...")
    
    try:
        # Initialize database and get engine
        db_engine, _ = init_database()
        print("Database connection established.")
        # Log basic engine info
        print(f"Engine URL: {str(db_engine.url)}")
        
        print("Creating tables...")
        print(f"Models registered: {list(Base.metadata.tables.keys())}")
        create_tables()
        print("All tables created successfully!")
        
        # Verify connection details and tables using SQL / inspector
        from sqlalchemy import inspect, text  # type: ignore[import]

        dialect = db_engine.url.get_backend_name()

        if dialect.startswith("postgresql"):
            # PostgreSQL-specific connection details
            with db_engine.connect() as conn:
                info_row = conn.execute(
                    text(
                        """
                        SELECT
                            current_database(),
                            current_user,
                            inet_server_addr(),
                            inet_server_port(),
                            current_schema()
                        """
                    )
                ).fetchone()

            db_name, db_user, db_host, db_port, db_schema = info_row
            print(
                "\nConnection details:"
                f"\n  current_database = {db_name}"
                f"\n  current_user     = {db_user}"
                f"\n  inet_server_addr = {db_host}"
                f"\n  inet_server_port = {db_port}"
                f"\n  current_schema   = {db_schema}"
            )
        else:
            # Generic info for non-PostgreSQL (e.g. SQLite)
            print(f"\nConnection details: dialect = {dialect}, URL = {db_engine.url}")

        # Verify tables were created (introspection works for both)
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        print(f"\nTables in database (via inspector): {tables}")
        
        if tables:
            print(f"\n✅ Successfully created {len(tables)} table(s):")
            for table in sorted(tables):
                print(f"   - {table}")
        else:
            print("\n⚠️  Warning: No tables found in database!")
        
        print("\nDatabase initialization complete!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

