from flask import jsonify, request
from app import db
from app.models import Product, Category, Contact
from app.routes import api_bp

@api_bp.route('/products', methods=['GET'])
def get_products():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', type=str)
    search = request.args.get('search', type=str)
    query = Product.query.filter_by(in_stock=True)
    if category:
        query = query.filter(Product.category.has(slug=category))
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    paginated = query.paginate(page=page, per_page=20)
    return jsonify({
        'products': [{
            'id': p.id, 'sku': p.sku, 'name': p.name, 'brand': p.brand,
            'price': p.display_price, 'in_stock': p.in_stock, 'image_url': p.image_url
        } for p in paginated.items],
        'total': paginated.total, 'pages': paginated.pages, 'current_page': page
    })

@api_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.filter_by(parent_id=None).all()
    return jsonify({'categories': [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in categories]})

@api_bp.route('/contact', methods=['POST'])
def create_contact():
    data = request.get_json()
    if not data or not data.get('name') or not data.get('email'):
        return jsonify({'error': 'Missing fields'}), 400
    contact = Contact(name=data['name'], email=data['email'], phone=data.get('phone'), message=data.get('message'))
    db.session.add(contact)
    db.session.commit()
    return jsonify({'success': True}), 201
