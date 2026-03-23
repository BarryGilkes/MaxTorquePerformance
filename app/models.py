from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255))
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    products = db.relationship('Product', backref='category', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turn14_item_id = db.Column(db.String(255), unique=True)
    sku = db.Column(db.String(255), nullable=False, unique=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    brand = db.Column(db.String(255))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    turn14_price = db.Column(db.Float)
    markup_percent = db.Column(db.Float, default=0)
    display_price = db.Column(db.Float)
    turn14_stock = db.Column(db.Integer, default=0)
    in_stock = db.Column(db.Boolean, default=True)
    image_url = db.Column(db.Text)
    fitment_ids = db.Column(db.Text)
    carb_compliant = db.Column(db.Boolean, default=False)
    featured = db.Column(db.Boolean, default=False)
    length = db.Column(db.Float)
    width = db.Column(db.Float)
    height = db.Column(db.Float)
    weight = db.Column(db.Float)
    weight_unit = db.Column(db.String(10), default='lb')
    local_notes = db.Column(db.Text)
    last_synced = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def calculate_display_price(self):
        if self.turn14_price:
            self.display_price = self.turn14_price * (1 + self.markup_percent / 100)
        return self.display_price

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    message = db.Column(db.Text, nullable=False)
    interested_products = db.Column(db.Text)
    status = db.Column(db.String(50), default='new')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SyncLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(255))
    status = db.Column(db.String(50))
    items_synced = db.Column(db.Integer)
    error_message = db.Column(db.Text)
    duration_seconds = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProductAttributeVisibility(db.Model):
    __tablename__ = 'product_attribute_visibility'
    id = db.Column(db.Integer, primary_key=True)
    attribute_name = db.Column(db.String(100), unique=True, nullable=False)
    is_visible = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
