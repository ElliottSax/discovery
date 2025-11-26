#!/usr/bin/env python3
"""Create only new tables, skip existing ones"""

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

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect, text
from api.database import DATABASE_URL

print("Creating engine...")
engine = create_engine(DATABASE_URL)

print("Checking connection...")
with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
print("✓ Connected to database\n")

# Get existing tables
inspector = inspect(engine)
existing_tables = inspector.get_table_names()
print(f"Existing tables: {', '.join(existing_tables)}\n")

# Tables we need to create
from api.db_models import Stock, PriceHistory, Pattern, Alert, AnalysisRun, Subscription

tables_to_create = [
    (Stock.__table__, 'stocks'),
    (PriceHistory.__table__, 'price_history'),
    (Pattern.__table__, 'patterns'),
    (Alert.__table__, 'alerts'),
    (AnalysisRun.__table__, 'analysis_runs'),
    (Subscription.__table__, 'subscriptions'),
]

print("Creating new tables...")
for table, name in tables_to_create:
    if name not in existing_tables:
        try:
            table.create(engine, checkfirst=True)
            print(f"  ✓ Created {name}")
        except Exception as e:
            print(f"  ✗ Failed to create {name}: {e}")
    else:
        print(f"  - {name} already exists")

print("\n✓ Database setup complete!")
print("\nAll tables:")
inspector = inspect(engine)
for table in sorted(inspector.get_table_names()):
    print(f"  • {table}")
