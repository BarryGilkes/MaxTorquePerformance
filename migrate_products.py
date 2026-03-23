#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/opt/maxtorque')
from app import db, create_app
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Add new columns to Product table if they don't exist
    columns_to_add = [
        ('length', 'FLOAT'),
        ('width', 'FLOAT'),
        ('height', 'FLOAT'),
        ('weight', 'FLOAT'),
        ('weight_unit', 'VARCHAR(10)')
    ]
    
    inspector = db.inspect(db.engine)
    existing_columns = [col['name'] for col in inspector.get_columns('product')]
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            stmt = text(f'ALTER TABLE product ADD COLUMN {col_name} {col_type}')
            try:
                db.session.execute(stmt)
                print(f"Added column: {col_name}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")
        else:
            print(f"Column already exists: {col_name}")
    
    db.session.commit()
    print("Migration completed.")
