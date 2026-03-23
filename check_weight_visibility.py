#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/maxtorque')
from app import create_app, db
from app.models import ProductAttributeVisibility

app = create_app()
with app.app_context():
    s = ProductAttributeVisibility.query.filter_by(attribute_name='weight').first()
    if s:
        print(f"weight.is_visible = {s.is_visible}")
    else:
        print("weight setting not found")
