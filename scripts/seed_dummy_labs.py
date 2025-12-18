#!/usr/bin/env python3
"""
Seed the database with 20 dummy labs for development/testing.

This script is safe to run multiple times; it will not duplicate labs
if they already exist.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_database, get_db  # type: ignore[import]
from src.models import Lab  # type: ignore[import]


DUMMY_LABS = [
    "Thermoelectric Materials Lab A",
    "Thermoelectric Materials Lab B",
    "Advanced Materials Lab",
    "Functional Oxides Lab",
    "Semiconductor Devices Lab",
    "Nanostructures Lab",
    "Energy Conversion Lab",
    "Thermal Transport Lab",
    "Low Temperature Physics Lab",
    "High Temperature Materials Lab",
    "Thin Films Lab",
    "Materials Characterization Lab",
    "Applied Physics Lab",
    "Solid State Chemistry Lab",
    "Electronic Materials Lab",
    "Surface Science Lab",
    "Quantum Materials Lab",
    "Instrument Development Lab",
    "Metrology Lab",
    "Collaborative Research Lab",
]


def main():
    print("Seeding dummy labs...")
    try:
        init_database()
        db = next(get_db())

        existing_names = {name for (name,) in db.query(Lab.name).all()}

        created = 0
        for name in DUMMY_LABS:
            if name in existing_names:
                continue
            lab = Lab(name=name, description=None, location=None, is_active=True)
            db.add(lab)
            created += 1

        if created:
            db.commit()

        print(f"Done. {created} new lab(s) created, {len(DUMMY_LABS) - created} already existed.")
    except Exception as e:
        print(f"Error seeding labs: {e}")
        sys.exit(1)
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    main()


