import os
import logging
from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Initialize SQLAlchemy with declarative base
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Initialize Flask-Login
login_manager = LoginManager()

def create_app():
    # Create Flask app
    app = Flask(__name__)

    # Email configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'unbugsolutionsti@gmail.com'
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

    # Initialize Mail
    from blueprints.orders import mail
    mail.init_app(app)
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # Configure database
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://postgres:HjxxdoOWOpOzjXXKRDeYSwRFsQEzMDms@switchyard.proxy.rlwy.net:23271/railway")
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_size": 5,
        "pool_recycle": 280,
        "pool_pre_ping": True,
        "pool_timeout": 30,
        "max_overflow": 10
    }
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ECHO"] = True  # Log SQL queries for debugging

    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'

    with app.app_context():
        # Import models
        from models import User, Employee, Client, Supplier, ServiceOrder, Project, StockItem, StoreItem, FinancialEntry

        # Create or update database tables
        try:
            db.create_all()
            db.session.commit()
            app.logger.info("Database tables created/updated successfully")
        except Exception as e:
            app.logger.error(f"Database initialization error: {str(e)}")
            db.session.rollback()
            raise

        # Create admin user if not exists
        from werkzeug.security import generate_password_hash
        from datetime import datetime

        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='admin',
                email='admin@unbug.com'
            )
            db.session.add(admin)
            db.session.flush()  # Para obter o ID do admin

            # Criar funcionário para o admin
            admin_employee = Employee(
                first_name='João',
                last_name='Silva',
                position='Gerente TI',
                department='TI',
                phone='(11) 91234-5678',
                hire_date=datetime.now().date(),
                active=True,
                user_id=admin.id
            )
            db.session.add(admin_employee)

            # Add predefined users
            users = [
                User(username='ceounbug', password_hash=generate_password_hash('unbug123'), 
                     role='management', email='ceo@unbug.com'),
                User(username='operacoesunbug', password_hash=generate_password_hash('unbug123'), 
                     role='management', email='operations@unbug.com'),
                User(username='rhunbug', password_hash=generate_password_hash('unbug123'), 
                     role='management', email='hr@unbug.com')
            ]
            db.session.add_all(users)
            db.session.flush()  # Para obter IDs dos usuários

            # Criar funcionários para os demais usuários
            employees = [
                Employee(
                    first_name='Roberto',
                    last_name='Costa',
                    position='CEO',
                    department='Diretoria',
                    phone='(11) 99876-5432',
                    hire_date=datetime.now().date(),
                    active=True,
                    user_id=users[0].id
                ),
                Employee(
                    first_name='Carlos',
                    last_name='Oliveira',
                    position='Gerente de Operações',
                    department='Operações',
                    phone='(11) 98765-4321',
                    hire_date=datetime.now().date(),
                    active=True,
                    user_id=users[1].id
                ),
                Employee(
                    first_name='Ana',
                    last_name='Souza',
                    position='Gerente de RH',
                    department='Recursos Humanos',
                    phone='(11) 97654-3210',
                    hire_date=datetime.now().date(),
                    active=True,
                    user_id=users[2].id
                )
            ]
            db.session.add_all(employees)
            db.session.commit()

        # Register blueprints
        from blueprints.auth import auth_bp
        from blueprints.dashboard import dashboard_bp
        from blueprints.orders import orders_bp
        from blueprints.finance import finance_bp
        from blueprints.stock import stock_bp
        from blueprints.employees import employees_bp
        from blueprints.clients import clients_bp
        from blueprints.security import security_bp
        from blueprints.reports import reports_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(orders_bp)
        app.register_blueprint(finance_bp)
        app.register_blueprint(stock_bp)
        app.register_blueprint(employees_bp)
        app.register_blueprint(clients_bp)
        app.register_blueprint(security_bp)
        app.register_blueprint(reports_bp)

        # Root route
        @app.route('/')
        def index():
            if current_user.is_authenticated:
                return redirect(url_for('dashboard.index'))
            return redirect(url_for('auth.login'))

        @login_manager.user_loader
        def load_user(user_id):
            from models import User
            return User.query.get(int(user_id))

        # Error handlers
        @app.errorhandler(Exception)
        def handle_error(error):
            app.logger.error(f'Unhandled error: {str(error)}')
            return 'Internal server error', 500

        return app

app = create_app()