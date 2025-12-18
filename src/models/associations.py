from sqlalchemy import Table, Column, Integer, ForeignKey
from src.database import Base

# Association table for multi-lab permissions (researchers with special access)
user_lab_permissions = Table(
    'user_lab_permissions',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('lab_id', Integer, ForeignKey('labs.id'), primary_key=True)
)

