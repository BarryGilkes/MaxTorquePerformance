from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///maxtorque.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'admin.login'

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.routes import api_bp, admin_bp, public_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(public_bp)

    with app.app_context():
        db.create_all()

    return app
