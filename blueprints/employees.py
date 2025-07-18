from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import Employee, User
from forms import EmployeeForm, EditEmployeeForm, SearchForm
from werkzeug.security import generate_password_hash
from datetime import datetime

employees_bp = Blueprint('employees', __name__, url_prefix='/employees')

@employees_bp.route('/')
@login_required
def index():
    search_form = SearchForm()
    
    # Query based on search parameters if any
    query = Employee.query
    
    if request.args.get('query'):
        search_term = f"%{request.args.get('query')}%"
        query = query.filter(Employee.first_name.like(search_term) | 
                            Employee.last_name.like(search_term) |
                            Employee.position.like(search_term) |
                            Employee.department.like(search_term))
    
    # Get all employees
    employees = query.order_by(Employee.first_name).all()
    
    return render_template('employees/index.html', 
                          employees=employees, 
                          search_form=search_form)

@employees_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # Only admin and management can create employees
    if not current_user.is_management():
        flash('Você não tem permissão para criar funcionários.', 'danger')
        return redirect(url_for('employees.index'))
    
    form = EmployeeForm()
    
    if form.validate_on_submit():
        # Check if username already exists
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user:
            flash('Nome de usuário já existe.', 'danger')
            return render_template('employees/create.html', form=form)
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash('Email já cadastrado.', 'danger')
            return render_template('employees/create.html', form=form)
        
        # Create user account
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=generate_password_hash(form.password.data),
            role=form.role.data
        )
        
        db.session.add(user)
        db.session.flush()  # This gives user.id a value before commit
        
        # Create employee profile
        employee = Employee(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            position=form.position.data,
            department=form.department.data,
            phone=form.phone.data,
            hire_date=form.hire_date.data,
            active=form.active.data,
            user_id=user.id
        )
        
        db.session.add(employee)
        db.session.commit()
        
        flash('Funcionário criado com sucesso!', 'success')
        return redirect(url_for('employees.index'))
    
    return render_template('employees/create.html', form=form)

@employees_bp.route('/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(employee_id):
    # Only admin and management can edit employees
    if not current_user.is_management():
        flash('Você não tem permissão para editar funcionários.', 'danger')
        return redirect(url_for('employees.index'))
    
    employee = Employee.query.get_or_404(employee_id)
    form = EditEmployeeForm(obj=employee)
    
    # Load user data
    if employee.user:
        form.email.data = employee.user.email
        form.role.data = employee.user.role
    
    if form.validate_on_submit():
        # Check if email already exists and is not the current user's email
        if employee.user:
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email and existing_email.id != employee.user.id:
                flash('Email já cadastrado.', 'danger')
                return render_template('employees/edit.html', form=form, employee=employee)
            
            # Update user account
            employee.user.email = form.email.data
            employee.user.role = form.role.data
        
        # Update employee profile
        employee.first_name = form.first_name.data
        employee.last_name = form.last_name.data
        employee.position = form.position.data
        employee.department = form.department.data
        employee.phone = form.phone.data
        employee.hire_date = form.hire_date.data
        employee.active = form.active.data
        
        db.session.commit()
        
        flash('Funcionário atualizado com sucesso!', 'success')
        return redirect(url_for('employees.index'))
    
    return render_template('employees/edit.html', form=form, employee=employee)

@employees_bp.route('/<int:employee_id>/delete', methods=['POST'])
@login_required
def delete(employee_id):
    # Only admin can delete employees
    if not current_user.is_admin():
        flash('Você não tem permissão para excluir funcionários.', 'danger')
        return redirect(url_for('employees.index'))
    
    employee = Employee.query.get_or_404(employee_id)
    
    # Store user_id to delete user after employee
    user_id = employee.user_id
    
    # Delete employee
    db.session.delete(employee)
    
    # Delete associated user if exists
    if user_id:
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
    
    db.session.commit()
    
    flash('Funcionário excluído com sucesso!', 'success')
    return redirect(url_for('employees.index'))

@employees_bp.route('/<int:employee_id>')
@login_required
def view(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    
    # Get employee service orders
    service_orders = employee.service_orders
    
    # Get employee projects
    projects = employee.projects
    
    from datetime import datetime
    return render_template('employees/view.html', 
                          employee=employee,
                          service_orders=service_orders,
                          projects=projects,
                          now=datetime.utcnow())
