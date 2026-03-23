import requests, os, json, re
from flask import render_template, request, current_app
from app.routes import public_bp
from app.models import Product, Category, ProductAttributeVisibility
from sqlalchemy import or_, and_

BRANDS_BY_LETTER = {
    '3': ['3D MAXpider'],
    'A': [
        'Access', 'Acerbis', 'ACL', 'ACT', 'Action Clutch', 'Addictive Desert Designs', 'Advan',
        'AEM', 'AEM Induction', 'Aeromotive', 'aFe', 'Agency Power', 'Air Lift', 'Airaid',
        'AirDog', 'Akrapovic', 'Alcon', 'All Balls Racing', 'AlphaRex', 'Alta', 'American Truxx',
        'AMP Research', 'AMP Tires', 'AMS', 'Anderson Composites', 'Answer', 'Antigravity Batteries',
        'ANZO', 'ARB', 'ARP', 'Arrowhead', 'Artec Industries', 'AST', 'Athena', 'ATI',
        'ATS Diesel', 'Atturo Tire', 'AutoMeter', 'Avon Tyre', 'AVS', 'AWE Tuning'
    ],
    'B': [
        'BackRack', 'Badlands', 'Baja Designs', 'BAK', 'Banks Power', 'Battery Tender',
        'Bazooka', 'BBK', 'BBS', 'BD Diesel', 'BedRug', 'Belak Wheels', 'Bell', 'Belltech',
        'BFGoodrich', 'Big Gun', 'BikeMaster', 'Bikers Choice', 'Bilstein', 'Bitubo Suspension',
        'BLOX Racing', 'BMC', 'BMR Suspension', 'Body Armor 4x4', 'BoostLine', 'BorgWarner',
        'Borla', 'Borne Off-Road', 'Bosch', 'Boss Audio', 'Boundary', 'Brembo', 'Brembo OE',
        'Brembo OE Powersports', 'Brian Crower', 'Bridgestone', 'Bully Dog', 'Burly Brand', 'Bushwacker'
    ],
    'C': [
        'Cali Off-Road', 'Cali Raised LED', 'Camburg', 'Carli', 'Carlisle Tires', 'Carrillo',
        'Chase Bays', 'Chemical Guys', 'Clevite', 'Clutch Masters', 'COBB', 'Cognito',
        'Cometic Gasket', 'COMP Cams', 'Comp1 Clutch', 'Competition Clutch', 'Continental Tire',
        'CORSA Performance', 'Covercraft', 'CP Pistons', 'CRG Constructors', 'CruzTOOLS', 'CSF',
        'CTEK', 'Cusco', 'Cycra', 'Cylinder Works'
    ],
    'D': [
        'DBA', 'DDP', 'DeatschWerks', 'Dee Zee', 'DEI', 'DFC', 'Diamond Eye Performance',
        'Diode Dynamics', 'Dirty Life', 'DKM Clutch', 'do88', 'Dowco', 'DragonFire Racing',
        'Driveshaft Shop', 'DS18', 'Dunlop', 'DV8 Offroad', 'Dynatek', 'Dynojet'
    ],
    'E': [
        'Eagle', 'Eaton', 'EBC', 'EBC Powersports', 'Edelbrock', 'EGR', 'Eibach',
        'Energy Suspension', 'Enkei', 'EPI', 'EVS', 'Excel', 'Exedy', 'Exergy', 'Extang'
    ],
    'F': [
        'Fabtech', 'FASS Fuel Systems', 'FAST', 'Fel-Pro', 'Ferrea', 'Fidanza', 'fifteen52',
        'Firestone', 'FIRSTGEAR', 'Fishbone Offroad', 'Fleece Performance', 'Fluidampr',
        'FMF Racing', 'Forced Performance', 'Ford Racing', 'Forgestar', 'FOX', 'FOX Powersports',
        'Fragola', 'FTI Performance', 'Fuelab'
    ],
    'G': [
        'Gaerne', 'Garrett', 'Gates', 'GEN-Y Hitch', 'GET', 'Giant Loop', 'Gibson', 'GiroDisc',
        'GMZ Race Products', 'Go Fast Bits', 'Go Rhino', 'Goodridge', 'Gram Lights', 'Grams Performance',
        'Granatelli Motor Sports', 'GReddy', 'GrimmSpeed', 'Griots Garage', 'GSC Power Division'
    ],
    'H': [
        'H&R', 'Haltech', 'Hardline', 'Hawk Performance', 'Hella', 'Hellwig', 'Hiflo Filter',
        'Hinson Clutch', 'HKS', 'Hot Cams', 'Hot Rods', 'Hotchkis', 'HP Tuners', 'Husky Liners'
    ],
    'I': [
        'ICON', 'Industrial Injection', 'Injector Dynamics', 'Injen', 'Innovate Motorsports',
        'Innovative Mounts', 'Invidia', 'ION Wheels', 'ISC Suspension', 'ISR Performance', 'ITP'
    ],
    'J': [
        'J&L', 'JBA', 'JE Pistons', 'Jets', 'JKS Manufacturing', 'JLT'
    ],
    'K': [
        'K&N Engineering', 'K1 Technologies', 'Kansei', 'Kartboy', 'KC HiLiTES', 'Kenda',
        'Kentrol', 'KFI', 'King Engine Bearings', 'King Shocks', 'Kleinn Air Horns', 'KONI',
        'Konig', 'Kooks Headers', 'Koyo', 'KraftWerks', 'Kraze Wheels', 'Kuryakyn', 'KW',
        'KYB', 'KYB Powersports'
    ],
    'L': [
        'LEER Group', 'Letric Lighting', 'LIQUI MOLY', 'LUND'
    ],
    'M': [
        'Magnaflow', 'Mahle', 'Mahle OE', 'Mamba', 'Manley Performance', 'Matrix Concepts',
        'Maxima', 'Maxtrac', 'Maxtrax', 'Maxxis', 'Mayhem', 'MBRP', 'McGard', 'McLeod Racing',
        'Method Wheels', 'MGP', 'Michelin', 'Mickey Thompson', 'Mishimoto', 'MOMO', 'Moog',
        'Moroso', 'Motion Pro', 'Moton', 'MOTOREX', 'Motul', 'mountune', 'Mustang Motorcycle', 'MXP'
    ],
    'N': [
        'N-Fab', 'Nacho Offroad Technology', 'NAMZ', 'Nankang', 'National Cycle', 'New Rage Cycles',
        'New Ray Toys', 'NGK', 'Nitrous Express', 'Nomad', 'NRG', 'Nuetech TUbliss'
    ],
    'O': [
        'Odyssey Battery', 'Ohlins', 'Old Man Emu', 'OMIX', 'OMP', 'ORACLE Lighting', 'OS Giken'
    ],
    'P': [
        'Pace Edwards', 'Pedders', 'Performance Machine', 'Perrin Performance', 'Peterson Fluid Systems',
        'Pivot Works', 'PowerStop', 'ProFilter', 'Progress LT', 'Progress Technology', 'Progressive',
        'Project Kics', 'Project Mu', 'ProTaper', 'Prothane', 'ProX', 'PRP Seats',
        'Pure Drivetrain Solutions', 'Putco'
    ],
    'Q': ['QA1', 'QTP', 'QuadBoss'],
    'R': [
        'R1 Concepts', 'Race Ramps', 'Race Star', 'Raceline', 'Racequip', 'Radium Engineering',
        'Raised Wheels', 'Rally Armor', 'Rampage', 'Rancho', 'Raxiom', 'Rays', 'Recaro',
        'Red Line', 'REDARC', 'Remark', 'Remus', 'Renthal', 'Retrax', 'Revel',
        'Revolution Gear & Axle', 'Rhino USA', 'Rhino-Rack', 'Ricks Motorsport Electrics',
        'Ridetech', 'Ridler Wheels', 'Rigid Industries', 'Rival 4x4', 'RK Chain', 'Road Armor',
        'Rock Krawler', 'Rock Slide Engineering', 'Rockford Fosgate', 'Rockford Fosgate UTV',
        'RockJock', 'Roll-N-Lock', 'Roush', 'Royal Purple', 'RS-R', 'Rugged Radios',
        'Rugged Ridge', 'Russell', 'RustBuster', 'Rywire'
    ],
    'S': [
        'S&S Cycle', 'SCT Performance', 'SeaSucker', 'Seibon', 'Seizmik', 'Sena Technologies',
        'SHW Performance', 'Sinister Diesel', 'Skunk2 Racing', 'Skyjacker', 'SLP', 'Smarty',
        'Snow Performance', 'Sound Off Recreational', 'South Bend Clutch', 'SPAL', 'SPARCO',
        'SPC Performance', 'SPEC', 'Spectre', 'Speed and Strength', 'SpeedStrap', 'SPL Parts',
        'SPOD', 'SPYDER', 'SSR', 'ST Suspensions', 'Stainless Bros', 'Stainless Works',
        'Stampede', 'Stoptech', 'Superlift', 'Superpro', 'Supertech', 'Superwinch', 'Synergy Mfg'
    ],
    'T': [
        'Tanabe', 'Tazer', 'Tein', 'Tensor Tire', 'Thule', 'TiALSport', 'Ticon', 'Timbren',
        'Titan Fuel Tanks', 'Tonno Pro', 'Torque Solution', 'Touren', 'TOYO', 'Tradesman',
        'Truxedo', 'Tuff Country', 'Tuffy Products', 'Turbo XS', 'Turbosmart', 'Turn 14 Distribution',
        'TURN Offroad', 'TwinPower'
    ],
    'U': [
        'Ultimax', 'UMI Performance', 'Undercover', 'Uni Filter', 'USWE'
    ],
    'V': [
        'Vance and Hines', 'Versus', 'Vertex Pistons', 'Vibrant', 'Victor Reinz', 'Vivid Racing',
        'Volant', 'Vortex Racing', 'Vossen'
    ],
    'W': [
        'Wagner Tuning', 'Walbro', 'Weapon R', 'WeatherTech', 'Wehrli', 'Weigh Safe', 'Weld',
        'Westin', 'Wheel Mate', 'Whiteline', 'Willie & Max', 'Wilwood', 'Wiseco'
    ],
    'X': ['XCLUTCH', 'XKGLOW', 'Xtreme Machine', 'XTrig'],
    'Y': ['Yokohama Tire', 'Yuasa Battery', 'Yukon Gear & Axle'],
    'Z': ['Zone Offroad']
}

@public_bp.route('/')
def home():
    # Get featured products (featured and in stock, with valid display_price)
    featured = Product.query.filter(
        Product.featured == True,
        Product.in_stock == True,
        Product.display_price.isnot(None)
    ).order_by(Product.created_at.desc()).limit(4).all()
    
    # If we have fewer than 4 featured products, supplement with recent in-stock products
    if len(featured) < 4:
        existing_ids = [p.id for p in featured]
        additional = Product.query.filter(
            Product.in_stock == True,
            Product.display_price.isnot(None),
            ~Product.id.in_(existing_ids)
        ).order_by(Product.created_at.desc()).limit(4 - len(featured)).all()
        featured_products = featured + additional
    else:
        featured_products = featured
    
    # Build hierarchical categories: [(root, [children])] for collapsible dropdown
    roots = Category.query.filter_by(parent_id=None).order_by(Category.name).all()
    category_tree = []
    for root in roots:
        children = Category.query.filter_by(parent_id=root.id).order_by(Category.name).all()
        category_tree.append((root, children))
    categories = category_tree
    return render_template('index.html', featured_products=featured_products, categories=categories)

@public_bp.route('/catalog')
def catalog():
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category', type=str)
    search = request.args.get('search', type=str)
    brand = request.args.get('brand', type=str)
    query = Product.query.filter_by(in_stock=True)
    if category_slug:
        # Get the category by slug
        category = Category.query.filter_by(slug=category_slug).first()
        if category:
            if category.parent_id is None:
                # Root category: include its subcategories' products as well
                child_ids = [c.id for c in Category.query.filter_by(parent_id=category.id).all()]
                allowed_ids = [category.id] + child_ids
                query = query.filter(Product.category_id.in_(allowed_ids))
            else:
                # Subcategory: only its own products
                query = query.filter(Product.category_id == category.id)
        else:
            # Invalid slug: no results
            query = query.filter(False)
    if search:
        words = search.split()
        if words:
            # Each word must appear in sku, name, or description
            word_filters = []
            for w in words:
                like = f'%{w}%'
                word_filters.append(or_(Product.sku.ilike(like), Product.name.ilike(like), Product.description.ilike(like)))
            query = query.filter(and_(*word_filters))
    if brand:
        query = query.filter(Product.brand.ilike(f'%{brand}%'))
    paginated = query.paginate(page=page, per_page=12)
    # Build hierarchical categories: [(root, [children])] for collapsible dropdown
    roots = Category.query.filter_by(parent_id=None).order_by(Category.name).all()
    category_tree = []
    for root in roots:
        children = Category.query.filter_by(parent_id=root.id).order_by(Category.name).all()
        category_tree.append((root, children))
    categories = category_tree
    visibility = {v.attribute_name: v.is_visible for v in ProductAttributeVisibility.query.all()}
    return render_template('catalog.html', products=paginated.items, categories=categories, pagination=paginated, attribute_visibility=visibility)

@public_bp.route('/brands')
def brands():
    base = os.getenv('TURN14_API_URL', 'https://apitest.turn14.com')
    cid = os.getenv('TURN14_CLIENT_ID')
    csec = os.getenv('TURN14_CLIENT_SECRET')
    grouped = {}
    try:
        token_resp = requests.post(
            f"{base}/v1/token",
            data={"client_id": cid, "client_secret": csec, "grant_type": "client_credentials"},
            timeout=10
        )
        if not token_resp.ok:
            raise Exception(f"Token error: {token_resp.status_code}")
        token = token_resp.json()['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        br = requests.get(f"{base}/v1/brands", headers=headers, timeout=10)
        if not br.ok:
            raise Exception(f"Brands error: {br.status_code}")
        data = br.json()
        brands_list = data.get('data', [])
        for brand in sorted(brands_list, key=lambda x: x['attributes']['name']):
            name = brand['attributes']['name']
            logo = brand['attributes'].get('logo')
            letter = name[0].upper()
            if letter not in grouped:
                grouped[letter] = []
            grouped[letter].append({'name': name, 'logo': logo})
    except Exception as e:
        current_app.logger.error(f"Turn14 API error, falling back to static brands: {e}")
        for letter, names in STATIC_BRANDS_BY_LETTER.items():
            grouped[letter] = [{'name': n, 'logo': None} for n in sorted(names)]
    return render_template('brands.html', grouped=grouped)

@public_bp.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    visibility = {v.attribute_name: v.is_visible for v in ProductAttributeVisibility.query.all()}
    return render_template('product_detail.html', product=product, attribute_visibility=visibility)

@public_bp.route('/contact')
def contact():
    return render_template('contact.html')
