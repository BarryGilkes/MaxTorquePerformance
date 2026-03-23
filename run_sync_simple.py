#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/opt/maxtorque')
from app import create_app, db
from app.models import Product, Category
from app.services.turn14 import get_turn14_token, get_or_create_category
import requests
from datetime import datetime

app = create_app()
with app.app_context():
    token = get_turn14_token()
    if not token:
        print("Failed to get Turn14 token")
        sys.exit(1)

    headers = {"Authorization": f"Bearer {token}"}
    page = 1
    synced = 0
    batch_commit = 50
    sku_map = {}
    category_cache = {}
    
    print("Starting sync...")
    while True:
        r = requests.get(f"https://apitest.turn14.com/v1/items", params={"page": page, "limit": 100}, headers=headers, timeout=30)
        if r.status_code == 429:
            print(f"Rate limited at page {page}")
            break
        if r.status_code != 200:
            print(f"HTTP {r.status_code} at page {page}")
            break
        items = r.json().get('data', [])
        if not items:
            break

        for item in items:
            attrs = item.get('attributes', {})
            item_id = item['id']
            sku = attrs.get('part_number') or attrs.get('mfr_part_number') or str(item_id)
            sku = str(sku)

            if sku in sku_map:
                product = sku_map[sku]
            else:
                product = Product.query.filter_by(sku=sku).first()
                if not product:
                    product = Product(sku=sku, turn14_item_id=item_id)
                else:
                    product.turn14_item_id = item_id
                sku_map[sku] = product

            product.name = attrs.get('product_name') or attrs.get('part_description') or sku
            product.brand = attrs.get('brand') or 'Unknown'
            product.description = attrs.get('part_description')
            product.image_url = attrs.get('thumbnail')
            can_order = any(loc.get('can_place_order', False) for loc in attrs.get('warehouse_availability', []))
            product.turn14_stock = 1 if can_order else 0
            product.in_stock = can_order
            dims = attrs.get('dimensions')
            if dims and isinstance(dims, list) and len(dims) > 0:
                first = dims[0]
                product.length = first.get('length')
                product.width = first.get('width')
                product.height = first.get('height')
                product.weight = first.get('weight')
            else:
                product.length = attrs.get('length') or attrs.get('item_length')
                product.width = attrs.get('width') or attrs.get('item_width')
                product.height = attrs.get('height') or attrs.get('item_height')
                product.weight = attrs.get('weight') or attrs.get('item_weight')
            if attrs.get('weight_unit'):
                product.weight_unit = attrs.get('weight_unit')
            else:
                product.weight_unit = 'lb'
            product.turn14_price = 0
            product.markup_percent = 0
            product.display_price = 0
            product.last_synced = datetime.utcnow()

            # Category assignment (same as original)
            cat_name = attrs.get('category')
            subcat_name = attrs.get('subcategory')
            if cat_name:
                if subcat_name:
                    parent_slug = cat_name.lower().replace(' ', '-')
                    parent = category_cache.get(parent_slug)
                    if not parent:
                        parent = Category.query.filter_by(slug=parent_slug, parent_id=None).first()
                        if not parent:
                            parent = Category(name=cat_name, slug=parent_slug)
                            db.session.add(parent)
                            db.session.flush()
                        category_cache[parent_slug] = parent
                    subcat_slug = subcat_name.lower().replace(' ', '-')
                    child_key = (subcat_slug, parent.id)
                    category = category_cache.get(child_key)
                    if not category:
                        category = Category.query.filter_by(slug=subcat_slug, parent_id=parent.id).first()
                        if not category:
                            category = Category(name=subcat_name, slug=subcat_slug, parent_id=parent.id)
                            db.session.add(category)
                            db.session.flush()
                        category_cache[child_key] = category
                    product.category = category
                else:
                    cat_slug = cat_name.lower().replace(' ', '-')
                    category = category_cache.get(cat_slug)
                    if not category:
                        category = Category.query.filter_by(slug=cat_slug, parent_id=None).first()
                        if not category:
                            category = Category(name=cat_name, slug=cat_slug)
                            db.session.add(category)
                            db.session.flush()
                        category_cache[cat_slug] = category
                    product.category = category

            db.session.add(product)
            synced += 1
            if synced % batch_commit == 0:
                db.session.commit()
                print(f"Committed {synced} products...")

        page += 1

    db.session.commit()
    print(f"Sync completed. Total products: {synced}")
