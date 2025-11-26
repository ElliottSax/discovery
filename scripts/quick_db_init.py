#!/usr/bin/env python3
"""Quick database initialization with environment loading"""

import os
import sys
from pathlib import Path

# Load .env file
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    print("✓ Environment variables loaded from .env")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.database import Base, engine, check_connection
from api.db_models import *

print("\n=== Database Initialization ===\n")

# Check connection
print("Checking database connection...")
if not check_connection():
    print("✗ Cannot connect to database")
    print(f"  URL: postgresql://{os.getenv('DB_USER')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}")
    sys.exit(1)

print("✓ Database connection successful\n")

# Create tables
print("Creating tables...")
try:
    Base.metadata.create_all(bind=engine)
    print("✓ All tables created successfully\n")
except Exception as e:
    print(f"✗ Failed to create tables: {e}")
    sys.exit(1)

# List tables
print("Tables created:")
for table in Base.metadata.sorted_tables:
    print(f"  • {table.name}")

print("\n✓ Database initialization complete!")
