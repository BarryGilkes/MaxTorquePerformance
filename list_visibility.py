#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/maxtorque')
from app import create_app, db
from app.models import ProductAttributeVisibility

app = create_app()
with app.app_context():
    settings = ProductAttributeVisibility.query.order_by(ProductAttributeVisibility.attribute_name).all()
    for s in settings:
        print(f"{s.attribute_name}: {s.is_visible}")
