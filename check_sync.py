#!/usr/bin/env python3
import os
from app import create_app
from app.models import Category, SyncLog, db

app = create_app()
with app.app_context():
    print("=== Checking category counts ===")
    total = Category.query.count()
    top = Category.query.filter_by(parent_id=None).count()
    print(f"Before sync: Total categories = {total}, Top-level = {top}")

from app.services.turn14 import get_turn14_token, sync_products_from_turn14
token = get_turn14_token()
print(f"Token obtained: {bool(token)}")

print("Starting sync...")
sync_products_from_turn14()

with app.app_context():
    total2 = Category.query.count()
    top2 = Category.query.filter_by(parent_id=None).count()
    latest = SyncLog.query.filter_by(endpoint='products').order_by(SyncLog.id.desc()).first()
    print(f"After sync: Total categories = {total2}, Top-level = {top2}")
    if latest:
        print(f"SyncLog: status={latest.status}, items={latest.items_synced}, error={latest.error_message}")
    else:
        print("No SyncLog entry found")
    db.session.commit()
