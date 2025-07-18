from app import db
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import ForeignKey, func, event
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='employee')  # admin, management, employee
    _is_active = db.Column("is_active", db.Boolean, default=True)  # Usando um alias para a coluna
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Override get_id para compatibilidade com Flask-Login
    def get_id(self):
        return str(self.id)

    # Override is_active do UserMixin
    @property
    def is_active(self):
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        self._is_active = value

    # Relationship to Employee (optional)
    employee = relationship("Employee", back_populates="user", uselist=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_management(self):
        return self.role == 'management' or self.role == 'admin'

    def has_security_access(self):
        return self.role == 'admin'

    def has_finance_access(self):
        return self.role in ['admin', 'management']

    def can_delete(self):
        return self.role in ['admin', 'management']

    def get_role_display(self):
        role_names = {
            'admin': 'Administrador',
            'management': 'Gerência',
            'employee': 'Funcionário'
        }
        return role_names.get(self.role, self.role)


class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    position = db.Column(db.String(100))
    department = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    hire_date = db.Column(db.Date, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to User
    user_id = db.Column(db.Integer, ForeignKey('user.id'))
    user = relationship("User", back_populates="employee")

    # Relationship to ServiceOrder
    service_orders = relationship("ServiceOrder", back_populates="employee")

    # Relationship to Project
    projects = relationship("Project", back_populates="manager")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    contact_person = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    service_orders = relationship("ServiceOrder", back_populates="client")
    projects = relationship("Project", back_populates="client")
    financial_entries = relationship("FinancialEntry", back_populates="client")


class Supplier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(100))
    state = db.Column(db.String(50))
    zip_code = db.Column(db.String(20))
    contact_person = db.Column(db.String(100))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    stock_items = relationship("StockItem", back_populates="supplier")
    store_items = relationship("StoreItem", back_populates="supplier")
    financial_entries = relationship("FinancialEntry", back_populates="supplier")


class ServiceOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open')  # open, in_progress, completed, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client_id = db.Column(db.Integer, ForeignKey('client.id'))
    client = relationship("Client", back_populates="service_orders")

    employee_id = db.Column(db.Integer, ForeignKey('employee.id'))
    employee = relationship("Employee", back_populates="service_orders")

    # Items used in the service order
    items_used = relationship("OrderItem", back_populates="service_order")

    # Financial entries related to this order
    financial_entries = relationship("FinancialEntry", back_populates="service_order")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    service_order_id = db.Column(db.Integer, ForeignKey('service_order.id'))
    service_order = relationship("ServiceOrder", back_populates="items_used")

    inventory_item_id = db.Column(db.Integer, ForeignKey('stock_item.id'))
    inventory_item = relationship("StockItem")


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='planning')  # planning, in_progress, on_hold, completed, cancelled
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    budget = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client_id = db.Column(db.Integer, ForeignKey('client.id'))
    client = relationship("Client", back_populates="projects")

    manager_id = db.Column(db.Integer, ForeignKey('employee.id'))
    manager = relationship("Employee", back_populates="projects")

    # Financial entries related to this project
    financial_entries = relationship("FinancialEntry", back_populates="project")


class StockItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50), unique=True)
    category = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=0)
    minimum_stock = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10, 2))
    location = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier_id = db.Column(db.Integer, ForeignKey('supplier.id'))
    supplier = relationship("Supplier", back_populates="stock_items")

    def is_low_stock(self):
        return self.quantity <= self.minimum_stock

class StoreItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    sku = db.Column(db.String(50), unique=True)
    category = db.Column(db.String(100))
    quantity = db.Column(db.Integer, default=0)
    minimum_stock = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10, 2))
    location = db.Column(db.String(100))
    image_url = db.Column(db.String(300))
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    supplier_id = db.Column(db.Integer, ForeignKey('supplier.id'))
    supplier = relationship("Supplier", back_populates="store_items")

    def is_low_stock(self):
        return self.quantity <= self.minimum_stock


class FinancialEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(20), nullable=False)  # income, expense
    category = db.Column(db.String(100))
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    invoice_number = db.Column(db.String(100))
    payment_method = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships - all optional depending on the type of entry
    client_id = db.Column(db.Integer, ForeignKey('client.id'))
    client = relationship("Client", back_populates="financial_entries")

    supplier_id = db.Column(db.Integer, ForeignKey('supplier.id'))
    supplier = relationship("Supplier", back_populates="financial_entries")

    service_order_id = db.Column(db.Integer, ForeignKey('service_order.id'))
    service_order = relationship("ServiceOrder", back_populates="financial_entries")

    project_id = db.Column(db.Integer, ForeignKey('project.id'))
    project = relationship("Project", back_populates="financial_entries")

    # File path for invoice/receipt if uploaded
    file_path = db.Column(db.String(300))


# Activity Log for system activities
class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    activity = db.Column(db.String(200), nullable=False)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(50), default='sistema')  # sistema, usuario, seguranca, etc

    # User relationship (optional - if activity is related to a user)
    user_id = db.Column(db.Integer, ForeignKey('user.id'), nullable=True)
    user = relationship("User", backref=db.backref("activities", lazy="dynamic"))
    
    @staticmethod
    def log_activity(username, activity, ip_address=None, user_id=None, category='sistema'):
        log = ActivityLog(
            username=username,
            activity=activity,
            ip_address=ip_address,
            user_id=user_id,
            category=category
        )
        db.session.add(log)
        try:
            db.session.commit()
        except:
            db.session.rollback()


# Trigger to update inventory when items are used in orders
@event.listens_for(OrderItem, 'after_insert')
def decrease_inventory_on_order(mapper, connection, target):
    inventory_item = StockItem.query.get(target.inventory_item_id)
    if inventory_item and inventory_item.quantity >= target.quantity:
        inventory_item.quantity -= target.quantity
        db.session.commit()