# app/__init__.py
import os
from flask import Flask
from flask_login import LoginManager
from .models import db, User
from flask_migrate import Migrate

migrate = Migrate()

def create_app():
    # Use instance_relative_config to tell Flask the instance folder is outside the app package
    app = Flask(__name__, instance_relative_config=True) 
    
    # --- Configurations ---
    app.config.from_mapping(
        SECRET_KEY='a-very-secret-key-that-you-should-change',
        # This tells SQLAlchemy where to create the database inside the instance folder
        SQLALCHEMY_DATABASE_URI=f'sqlite:///{os.path.join(app.instance_path, "site.db")}',
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Set the upload folder path relative to the app package's static folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'profile_pics')
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # --- Initialize Extensions ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager = LoginManager(app)
    login_manager.login_view = 'main.login' 
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- Register Blueprints ---
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from . import analysis_utils
    with app.app_context():
        analysis_utils.initialize_models()

    return app