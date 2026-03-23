#!/usr/bin/env python3
import sys, requests, os
sys.path.insert(0, '/opt/maxtorque')
from app import create_app, db
from app.models import ProductAttributeVisibility
from flask_login import login_user
from app.models import User

# First, create a test user if none exists? Not needed; we'll just simulate POST with session.
# Instead, let's directly test the database update:
app = create_app()
with app.app_context():
    # Find weight setting
    weight_setting = ProductAttributeVisibility.query.filter_by(attribute_name='weight').first()
    if weight_setting:
        print(f"Before: weight is_visible = {weight_setting.is_visible}")
        weight_setting.is_visible = False
        db.session.commit()
        print("Updated to False")
        # Verify
        again = ProductAttributeVisibility.query.filter_by(attribute_name='weight').first()
        print(f"After: weight is_visible = {again.is_visible}")
    else:
        print("No weight setting found")
