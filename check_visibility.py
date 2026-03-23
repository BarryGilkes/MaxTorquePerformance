#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/maxtorque')
from app import create_app, db
from app.models import ProductAttributeVisibility

app = create_app()
with app.app_context():
    settings = ProductAttributeVisibility.query.all()
    for s in settings:
        print(f"{s.attribute_name}: is_visible = {s.is_visible}")
