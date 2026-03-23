#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/maxtorque')
from app import create_app, db
from app.models import Product

app = create_app()
with app.app_context():
    # Try by ID or SKU
    product = Product.query.filter_by(sku='ede41137').first()
    if not product:
        # Maybe it's stored as turn14_item_id?
        product = Product.query.filter_by(turn14_item_id='ede41137').first()
    
    if product:
        print(f"Product ID: {product.id}")
        print(f"SKU: {product.sku}")
        print(f"Name: {product.name}")
        print(f"Length: {product.length}")
        print(f"Width: {product.width}")
        print(f"Height: {product.height}")
        print(f"Weight: {product.weight}")
        print(f"Weight unit: {product.weight_unit}")
        print(f"Turn14 item ID: {product.turn14_item_id}")
    else:
        print("Product not found")
