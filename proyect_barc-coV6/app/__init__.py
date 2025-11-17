from flask import Flask
from pathlib import Path
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

BASE_DIR = Path(__file__).resolve().parent.parent

bcrypt = Bcrypt()                 
login_manager = LoginManager()
login_manager.login_view = "auth.login_get"

def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = "supersecretkey"
    app.config["DATABASE"] = str(BASE_DIR / "puerto.db")

    bcrypt.init_app(app)
    login_manager.init_app(app)


    from .routes import main, db as db_bp, program
    from app.envios import envios_bp
    app.register_blueprint(main)
    app.register_blueprint(db_bp)
    app.register_blueprint(program)
    app.register_blueprint(envios_bp)
    
    from .auth import auth
    app.register_blueprint(auth)
    return app