#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/maxtorque')
from app import create_app, db
from app.models import ProductAttributeVisibility

app = create_app()
with app.app_context():
    # Ensure turn14_item_id exists
    setting = ProductAttributeVisibility.query.filter_by(attribute_name='turn14_item_id').first()
    if not setting:
        setting = ProductAttributeVisibility(attribute_name='turn14_item_id', is_visible=True)
        db.session.add(setting)
        db.session.commit()
        print("Added turn14_item_id with default visible=True")
    else:
        print(f"turn14_item_id exists, is_visible = {setting.is_visible}")
