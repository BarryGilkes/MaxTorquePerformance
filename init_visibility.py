#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/opt/maxtorque')
from app import create_app, db
from app.models import ProductAttributeVisibility

app = create_app()
with app.app_context():
    # Default visible attributes
    defaults = [
        ('dimensions', True),
        ('weight', True)
    ]
    
    for attr_name, is_visible in defaults:
        existing = ProductAttributeVisibility.query.filter_by(attribute_name=attr_name).first()
        if not existing:
            setting = ProductAttributeVisibility(attribute_name=attr_name, is_visible=is_visible)
            db.session.add(setting)
            print(f"Added visibility setting: {attr_name} = {is_visible}")
        else:
            print(f"Setting already exists: {attr_name}")
    
    db.session.commit()
    print("Visibility defaults initialized.")
