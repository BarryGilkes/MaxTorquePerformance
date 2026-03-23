from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Product, Category, Contact, ProductAttributeVisibility, SyncLog
from sqlalchemy import or_
from app.routes import admin_bp
from datetime import datetime
from app.services.turn14 import sync_products_from_turn14

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('public.home'))

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    total_products = Product.query.count()
    total_contacts = Contact.query.count()
    new_contacts = Contact.query.filter_by(status='new').count()
    return render_template('admin/dashboard.html', total_products=total_products, total_contacts=total_contacts, new_contacts=new_contacts)

@admin_bp.route('/products')
@login_required
def products():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('q', '').strip()
    query = Product.query
    if search:
        like = f'%{search}%'
        query = query.filter(
            or_(
                Product.sku.ilike(like),
                Product.name.ilike(like),
                Product.description.ilike(like),
                Product.brand.ilike(like),
                Product.turn14_item_id.ilike(like),
                Product.category.has(name=like)
            )
        )
    paginated = query.paginate(page=page, per_page=20)
    return render_template('admin/products.html', products=paginated.items, pagination=paginated, search=search)

@admin_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
def product_create():
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        product = Product(
            sku=request.form.get('sku'),
            name=request.form.get('name'),
            brand=request.form.get('brand'),
            description=request.form.get('description'),
            turn14_price=float(request.form.get('turn14_price', 0)) if request.form.get('turn14_price') else None,
            markup_percent=float(request.form.get('markup_percent', 0)),
            turn14_stock=int(request.form.get('turn14_stock', 0)),
            in_stock=request.form.get('in_stock') == 'on',
            image_url=request.form.get('image_url'),
            fitment_ids=request.form.get('fitment_ids'),
            carb_compliant=request.form.get('carb_compliant') == 'on',
            local_notes=request.form.get('local_notes'),
            featured=request.form.get('featured') == 'on',
            turn14_item_id=request.form.get('turn14_item_id'),
            length=float(request.form.get('length')) if request.form.get('length') else None,
            width=float(request.form.get('width')) if request.form.get('width') else None,
            height=float(request.form.get('height')) if request.form.get('height') else None,
            weight=float(request.form.get('weight')) if request.form.get('weight') else None,
            weight_unit=request.form.get('weight_unit', 'lb')
        )
        product.calculate_display_price()
        category_id = request.form.get('category_id')
        if category_id:
            product.category_id = int(category_id)
        db.session.add(product)
        db.session.commit()
        flash('Product created successfully.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', categories=categories, product=None)

@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.name).all()
    if request.method == 'POST':
        product.sku = request.form.get('sku')
        product.name = request.form.get('name')
        product.brand = request.form.get('brand')
        product.description = request.form.get('description')
        product.turn14_price = float(request.form.get('turn14_price', 0)) if request.form.get('turn14_price') else None
        product.markup_percent = float(request.form.get('markup_percent', 0))
        product.turn14_stock = int(request.form.get('turn14_stock', 0))
        product.in_stock = request.form.get('in_stock') == 'on'
        product.image_url = request.form.get('image_url')
        product.fitment_ids = request.form.get('fitment_ids')
        product.carb_compliant = request.form.get('carb_compliant') == 'on'
        product.local_notes = request.form.get('local_notes')
        product.featured = request.form.get('featured') == 'on'
        product.turn14_item_id = request.form.get('turn14_item_id')
        product.length = float(request.form.get('length')) if request.form.get('length') else None
        product.width = float(request.form.get('width')) if request.form.get('width') else None
        product.height = float(request.form.get('height')) if request.form.get('height') else None
        product.weight = float(request.form.get('weight')) if request.form.get('weight') else None
        product.weight_unit = request.form.get('weight_unit', 'lb')
        product.calculate_display_price()
        category_id = request.form.get('category_id')
        if category_id:
            product.category_id = int(category_id)
        else:
            product.category_id = None
        db.session.commit()
        flash('Product updated successfully.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html', categories=categories, product=product)

@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def product_delete(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted.', 'danger')
    return redirect(url_for('admin.products'))

@admin_bp.route('/contacts')
@login_required
def contacts():
    page = request.args.get('page', 1, type=int)
    paginated = Contact.query.order_by(Contact.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/contacts.html', contacts=paginated.items, pagination=paginated)

@admin_bp.route('/categories')
@login_required
def categories():
    cats = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=cats)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
def category_create():
    parents = Category.query.all()
    if request.method == 'POST':
        cat = Category(
            name=request.form.get('name'),
            slug=request.form.get('slug'),
            description=request.form.get('description')
        )
        parent_id = request.form.get('parent_id')
        if parent_id:
            cat.parent_id = int(parent_id)
        db.session.add(cat)
        db.session.commit()
        flash('Category created.', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', parents=parents, category=None)

@admin_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def category_edit(category_id):
    cat = Category.query.get_or_404(category_id)
    parents = Category.query.filter(Category.id != category_id).all()
    if request.method == 'POST':
        cat.name = request.form.get('name')
        cat.slug = request.form.get('slug')
        cat.description = request.form.get('description')
        parent_id = request.form.get('parent_id')
        if parent_id:
            cat.parent_id = int(parent_id)
        else:
            cat.parent_id = None
        db.session.commit()
        flash('Category updated.', 'success')
        return redirect(url_for('admin.categories'))
    return render_template('admin/category_form.html', parents=parents, category=cat)

@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def category_delete(category_id):
    cat = Category.query.get_or_404(category_id)
    db.session.delete(cat)
    db.session.commit()
    flash('Category deleted.', 'danger')
    return redirect(url_for('admin.categories'))

@admin_bp.route('/sync-products')
@login_required
def sync_products():
    try:
        sync_products_from_turn14()
        flash('Turn14 product sync started. Check Sync Logs for details.', 'success')
    except Exception as e:
        flash(f'Sync failed: {str(e)}', 'danger')
    return redirect(url_for('admin.products'))

@admin_bp.route('/sync-logs')
@login_required
def sync_logs():
    page = request.args.get('page', 1, type=int)
    paginated = SyncLog.query.order_by(SyncLog.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/sync_logs.html', logs=paginated.items, pagination=paginated)

# New: Attribute visibility management
@admin_bp.route('/attributes')
@login_required
def attribute_visibility():
# Admin page to manage which product attributes are shown publicly.
    # Get all visibility settings, ordered by attribute_name
    settings = ProductAttributeVisibility.query.order_by(ProductAttributeVisibility.attribute_name).all()
    return render_template('admin/attributes.html', settings=settings)

@admin_bp.route('/api/admin/attributes/visibility', methods=['GET', 'POST'])
@login_required
def api_attribute_visibility():
    # API to get or update attribute visibility toggles.
    if request.method == 'GET':
        settings = ProductAttributeVisibility.query.order_by(ProductAttributeVisibility.attribute_name).all()
        result = {s.attribute_name: s.is_visible for s in settings}
        return jsonify(result)
    
    # POST: expects JSON: { attribute_name: is_visible, ... } or { updates: [{attribute_name: ..., is_visible: true}, ...] }
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Support both single object and array of updates
    updates = data.get('updates', [data] if 'attribute_name' in data else [])
    
    print(f"[DEBUG] Received updates: {updates}")  # Log to stdout
    
    for update in updates:
        attr_name = update.get('attribute_name')
        is_visible = update.get('is_visible')
        if attr_name is None or is_visible is None:
            print(f"[DEBUG] Skipping update with missing data: {update}")
            continue
        setting = ProductAttributeVisibility.query.filter_by(attribute_name=attr_name).first()
        if setting:
            print(f"[DEBUG] Updating {attr_name} to {is_visible}")
            setting.is_visible = bool(is_visible)
        else:
            print(f"[DEBUG] Creating new setting {attr_name} = {is_visible}")
            setting = ProductAttributeVisibility(attribute_name=attr_name, is_visible=bool(is_visible))
            db.session.add(setting)
    
    try:
        db.session.commit()
        print("[DEBUG] Commit successful")
    except Exception as e:
        print(f"[DEBUG] Commit failed: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    
    return jsonify({'success': True, 'updated': len(updates)})

from flask import flash, redirect, url_for

@admin_bp.route('/sync-prices')
@login_required
def sync_prices():
    from app.services.turn14 import sync_prices_from_turn14
    sync_prices_from_turn14()
    flash('Turn14 price sync completed.', 'success')
    return redirect(url_for('admin.sync_logs'))
