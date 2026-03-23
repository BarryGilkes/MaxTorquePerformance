#!/usr/bin/env python3
import sys
sys.path.insert(0, '/opt/maxtorque')
from app import create_app, db
from app.models import User
app = create_app()
with app.app_context():
    u = User.query.filter_by(email='admin@maxtorque.com').first()
    if not u:
        u = User(email='admin@maxtorque.com')
        u.set_password('adminpassword123')
        db.session.add(u)
        db.session.commit()
        print('Admin user created')
    else:
        print('Admin already exists')
