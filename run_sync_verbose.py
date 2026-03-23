#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/opt/maxtorque')
from app import create_app
from app.services.turn14 import sync_products_from_turn14
from datetime import datetime

app = create_app()
with app.app_context():
    print(f"[{datetime.utcnow()}] Starting sync...")
    try:
        sync_products_from_turn14()
        print(f"[{datetime.utcnow()}] Sync completed.")
    except Exception as e:
        print(f"[{datetime.utcnow()}] Sync failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
