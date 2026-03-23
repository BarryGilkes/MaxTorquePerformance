from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')
admin_bp = Blueprint('admin', __name__)
public_bp = Blueprint('public', __name__)

from app.routes import api, admin, public
