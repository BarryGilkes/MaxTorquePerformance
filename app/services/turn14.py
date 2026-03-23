import requests
import os
from datetime import datetime
from dotenv import load_dotenv
from app import db
from app.models import Product, SyncLog, Category

load_dotenv()

TURN14_BASE_URL = os.getenv('TURN14_API_URL', 'https://apitest.turn14.com')
CLIENT_ID = os.getenv('TURN14_CLIENT_ID')
CLIENT_SECRET = os.getenv('TURN14_CLIENT_SECRET')

def get_turn14_token():
    try:
        resp = requests.post(
            f"{TURN14_BASE_URL}/v1/token",
            data={"client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "grant_type": "client_credentials"},
            timeout=10
        )
        if resp.status_code != 200:
            return None
        return resp.json().get('access_token')
    except Exception as e:
        print(f"Token error: {e}")
        return None

def get_or_create_category(name, parent_name=None):
    name = name.strip()
    if not name:
        return None
    slug = name.lower().replace(' ', '-')
    parent_id = None
    if parent_name:
        parent_name = parent_name.strip()
        if parent_name:
            parent_slug = parent_name.lower().replace(' ', '-')
            parent = Category.query.filter_by(slug=parent_slug, parent_id=None).first()
            if not parent:
                parent = Category(name=parent_name, slug=parent_slug)
                db.session.add(parent)
                db.session.flush()
            parent_id = parent.id
    category = Category.query.filter_by(slug=slug, parent_id=parent_id).first()
    if not category:
        category = Category(name=name, slug=slug, parent_id=parent_id)
        db.session.add(category)
    return category

def sync_products_from_turn14():
    token = get_turn14_token()
    if not token:
        log_sync('products', 'failed', 0, 'No auth token')
        return

    headers = {"Authorization": f"Bearer {token}"}
    page = 1
    synced = 0
    batch_commit = 50
    sku_map = {}
    category_cache = {}
    try:
        while True:
            r = requests.get(f"{TURN14_BASE_URL}/v1/items", params={"page": page, "limit": 100}, headers=headers, timeout=10)
            if r.status_code == 429:
                log_sync('products', 'failed', synced, 'Rate limited')
                break
            if r.status_code != 200:
                log_sync('products', 'failed', synced, f'HTTP {r.status_code}')
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

                # Calculate stock quantity from warehouse_availability
                warehouses = attrs.get('warehouse_availability', [])
                total_quantity = 0
                can_order = False
                # Possible field names for quantity in warehouse objects
                quantity_fields = ['quantity', 'stock', 'available_quantity', 'qty', 'on_hand']
                for loc in warehouses:
                    # Determine if any warehouse allows ordering
                    if loc.get('can_place_order', False):
                        can_order = True
                    # Sum quantities from known fields
                    for field in quantity_fields:
                        qty = loc.get(field, 0)
                        if isinstance(qty, (int, float)):
                            total_quantity += int(qty)
                            break  # Use first found quantity field

                product.turn14_stock = total_quantity
                product.in_stock = (total_quantity > 0) and can_order

                product.turn14_price = 0
                product.markup_percent = 0
                product.display_price = 0
                product.last_synced = datetime.utcnow()

                # Extract dimensions and weight from dimensions array or flat fields
                dims = attrs.get('dimensions')
                if dims and isinstance(dims, list) and len(dims) > 0:
                    first = dims[0]
                    product.length = first.get('length')
                    product.width = first.get('width')
                    product.height = first.get('height')
                    product.weight = first.get('weight')
                else:
                    # Fallback to flat fields (legacy format)
                    product.length = attrs.get('length') or attrs.get('item_length')
                    product.width = attrs.get('width') or attrs.get('item_width')
                    product.height = attrs.get('height') or attrs.get('item_height')
                    product.weight = attrs.get('weight') or attrs.get('item_weight')
                # Keep default weight_unit = 'lb' unless API provides it
                if attrs.get('weight_unit'):
                    product.weight_unit = attrs.get('weight_unit')
                else:
                    product.weight_unit = 'lb'

                # Category assignment using slugs
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

            page += 1

        db.session.commit()
        log_sync('products', 'success', synced)
    except Exception as e:
        db.session.rollback()
        log_sync('products', 'failed', synced, str(e))

def log_sync(endpoint, status, count, error=None):
    log = SyncLog(endpoint=endpoint, status=status, items_synced=count, error_message=error)
    db.session.add(log)
    db.session.commit()

def sync_prices_from_turn14():
    """Fetch pricing from /v1/pricing and update product prices."""
    token = get_turn14_token()
    if not token:
        log_sync('prices', 'failed', 0, 'No auth token')
        return
    headers = {"Authorization": f"Bearer {token}"}
    page = 1
    updated = 0
    batch_commit = 100
    try:
        while True:
            r = requests.get(f"{TURN14_BASE_URL}/v1/pricing", params={"page": page}, headers=headers, timeout=10)
            if r.status_code == 429:
                log_sync('prices', 'failed', updated, 'Rate limited')
                break
            if r.status_code != 200:
                log_sync('prices', 'failed', updated, f'HTTP {r.status_code}')
                break
            data = r.json().get('data', [])
            if not data:
                break
            for item in data:
                attrs = item.get('attributes', {})
                turn14_id = str(item['id'])
                # Choose price: prefer MAP; else first pricelist; else purchase_cost
                price = None
                pricelists = attrs.get('pricelists', [])
                if isinstance(pricelists, list) and pricelists:
                    for pl in pricelists:
                        if pl.get('name') == 'MAP':
                            price = pl.get('price')
                            break
                    if price is None:
                        price = pricelists[0].get('price')
                if price is None:
                    price = attrs.get('purchase_cost')
                try:
                    price_val = float(price) if price is not None else 0.0
                except (ValueError, TypeError):
                    price_val = 0.0
                product = Product.query.filter_by(turn14_item_id=turn14_id).first()
                if product:
                    product.turn14_price = price_val
                    if product.markup_percent:
                        product.display_price = price_val * (1 + product.markup_percent / 100)
                    else:
                        product.display_price = price_val
                    db.session.add(product)
                    updated += 1
                    if updated % batch_commit == 0:
                        db.session.commit()
            page += 1
        db.session.commit()
        log_sync('prices', 'success', updated)
    except Exception as e:
        db.session.rollback()
        log_sync('prices', 'failed', updated, str(e))
