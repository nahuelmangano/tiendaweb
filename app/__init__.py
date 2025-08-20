import os
from flask import Flask, render_template,session
from flask_mail import Mail
from dotenv import load_dotenv
from .models import db, Role
from flask import redirect, url_for

mail = Mail()

def create_app():
    load_dotenv()
    app = Flask(__name__)

    # Configuración clave secreta
    app.secret_key = os.environ.get("SECRET_KEY", "clave_super_secreta_cambiame")

    # Configuración DB
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL',
        'postgresql://nmangano:tu_password_seguro@localhost/portfolio_db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    # Configuración Flask-Mail
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT'))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
    mail.init_app(app)

    # Crear carpetas necesarias
    UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

    # --- Registrar Blueprints ---
    from .auth.routes import auth_bp
    from .dashboard.routes import dashboard_bp
    from .tienda.routes import tienda_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tienda_bp)

    # Página de inicio
    @app.route("/")
    def index():
       return redirect(url_for("tienda.tienda"))

    @app.route("/reset_session")
    def reset_session():
        session.clear()
        return "Sesión reseteada"    
    # Crear tablas y roles
    with app.app_context():
        db.create_all()
        for role_name in ["admin", "user", "moderator"]:
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))
        db.session.commit()

    @app.context_processor
    def inject_carrito_count():
        carrito = session.get("carrito", [])
        cantidad = len(carrito)  # porque solo guardás IDs
        return dict(carrito_count=cantidad)
    return app
