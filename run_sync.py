#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, '/opt/maxtorque')
from app import create_app
from app.services.turn14 import sync_products_from_turn14

app = create_app()
with app.app_context():
    sync_products_from_turn14()
