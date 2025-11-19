from flask import Flask
from pathlib import Path
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()                 
login_manager = LoginManager()
login_manager.login_view = "auth.login_get"

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = "supersecretkey"

    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    with app.app_context():
        from app.db import init_db, close_db
        init_db()  # Crear tablas si no existen
        app.teardown_appcontext(close_db) 

    # Registrar blueprints...
    from .routes import main, db as db_bp, program
    from app.envios import envios_bp
    from app.admin import admin_bp
    from app.barcos import barcos_bp
    from .auth import auth
    
    app.register_blueprint(main)
    app.register_blueprint(db_bp)
    app.register_blueprint(program)
    app.register_blueprint(envios_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(barcos_bp)    
    app.register_blueprint(auth)
    
    return app