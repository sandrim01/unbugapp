from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from models import FinancialEntry, Client, Supplier, ServiceOrder, Project
from forms import FinancialEntryForm, SearchForm
from datetime import datetime
from sqlalchemy import func
import os
from werkzeug.utils import secure_filename
import uuid

finance_bp = Blueprint('finance', __name__, url_prefix='/finance')

@finance_bp.before_request
@login_required
def check_finance_access():
    # Check if the user has access to finance module
    if not current_user.has_finance_access():
        flash('Você não tem permissão para acessar o módulo financeiro.', 'danger')
        return redirect(url_for('dashboard.index'))

@finance_bp.route('/')
def index():
    search_form = SearchForm()
    
    # Query based on search parameters if any
    query = FinancialEntry.query
    
    if request.args.get('query'):
        search_term = f"%{request.args.get('query')}%"
        query = query.filter(FinancialEntry.description.like(search_term) | 
                             FinancialEntry.category.like(search_term))
    
    if request.args.get('status'):
        query = query.filter(FinancialEntry.type == request.args.get('status'))
    
    if request.args.get('date_from'):
        date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        query = query.filter(FinancialEntry.date >= date_from)
    
    if request.args.get('date_to'):
        date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
        query = query.filter(FinancialEntry.date <= date_to)
    
    # Calculate totals
    total_income = db.session.query(func.sum(FinancialEntry.amount)).filter(FinancialEntry.type == 'income').scalar() or 0
    total_expenses = db.session.query(func.sum(FinancialEntry.amount)).filter(FinancialEntry.type == 'expense').scalar() or 0
    balance = total_income - total_expenses
    
    # Get entries ordered by date (latest first)
    entries = query.order_by(FinancialEntry.date.desc()).all()
    
    return render_template('finance/index.html', 
                          entries=entries, 
                          search_form=search_form,
                          total_income=total_income,
                          total_expenses=total_expenses,
                          balance=balance)

@finance_bp.route('/create', methods=['GET', 'POST'])
def create_entry():
    form = FinancialEntryForm()
    
    # Populate the select fields with available options
    form.client_id.choices = [(0, 'Selecione um cliente')] + [(client.id, client.name) for client in Client.query.filter_by(active=True).all()]
    form.supplier_id.choices = [(0, 'Selecione um fornecedor')] + [(supplier.id, supplier.name) for supplier in Supplier.query.filter_by(active=True).all()]
    form.service_order_id.choices = [(0, 'Selecione uma ordem de serviço')] + [(order.id, f"#{order.id} - {order.title}") for order in ServiceOrder.query.all()]
    form.project_id.choices = [(0, 'Selecione um projeto')] + [(project.id, project.name) for project in Project.query.all()]
    
    if form.validate_on_submit():
        # Handle file upload if present
        file_path = None
        if form.invoice_file.data:
            # Create upload directory if it doesn't exist
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Generate unique filename
            original_filename = secure_filename(form.invoice_file.data.filename)
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Save the file
            file_path = os.path.join('uploads', unique_filename)
            form.invoice_file.data.save(os.path.join(current_app.root_path, 'static', file_path))
        
        # Create financial entry
        entry = FinancialEntry(
            type=form.type.data,
            category=form.category.data,
            amount=form.amount.data,
            description=form.description.data,
            date=form.date.data,
            invoice_number=form.invoice_number.data,
            payment_method=form.payment_method.data,
            file_path=file_path
        )
        
        # Set optional relationships
        if form.client_id.data and form.client_id.data != 0:
            entry.client_id = form.client_id.data
            
        if form.supplier_id.data and form.supplier_id.data != 0:
            entry.supplier_id = form.supplier_id.data
            
        if form.service_order_id.data and form.service_order_id.data != 0:
            entry.service_order_id = form.service_order_id.data
            
        if form.project_id.data and form.project_id.data != 0:
            entry.project_id = form.project_id.data
        
        db.session.add(entry)
        db.session.commit()
        
        flash('Lançamento financeiro criado com sucesso!', 'success')
        return redirect(url_for('finance.index'))
    
    return render_template('finance/create.html', form=form)

@finance_bp.route('/<int:entry_id>/edit', methods=['GET', 'POST'])
def edit_entry(entry_id):
    entry = FinancialEntry.query.get_or_404(entry_id)
    form = FinancialEntryForm(obj=entry)
    
    # Populate the select fields with available options
    form.client_id.choices = [(0, 'Selecione um cliente')] + [(client.id, client.name) for client in Client.query.filter_by(active=True).all()]
    form.supplier_id.choices = [(0, 'Selecione um fornecedor')] + [(supplier.id, supplier.name) for supplier in Supplier.query.filter_by(active=True).all()]
    form.service_order_id.choices = [(0, 'Selecione uma ordem de serviço')] + [(order.id, f"#{order.id} - {order.title}") for order in ServiceOrder.query.all()]
    form.project_id.choices = [(0, 'Selecione um projeto')] + [(project.id, project.name) for project in Project.query.all()]
    
    # Pre-select current values
    if entry.client_id:
        form.client_id.data = entry.client_id
    else:
        form.client_id.data = 0
        
    if entry.supplier_id:
        form.supplier_id.data = entry.supplier_id
    else:
        form.supplier_id.data = 0
        
    if entry.service_order_id:
        form.service_order_id.data = entry.service_order_id
    else:
        form.service_order_id.data = 0
        
    if entry.project_id:
        form.project_id.data = entry.project_id
    else:
        form.project_id.data = 0
    
    if form.validate_on_submit():
        # Handle file upload if present
        if form.invoice_file.data:
            # Remove old file if exists
            if entry.file_path:
                old_file_path = os.path.join(current_app.root_path, 'static', entry.file_path)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # Create upload directory if it doesn't exist
            uploads_dir = os.path.join(current_app.root_path, 'static/uploads')
            os.makedirs(uploads_dir, exist_ok=True)
            
            # Generate unique filename
            original_filename = secure_filename(form.invoice_file.data.filename)
            file_extension = os.path.splitext(original_filename)[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # Save the file
            file_path = os.path.join('uploads', unique_filename)
            form.invoice_file.data.save(os.path.join(current_app.root_path, 'static', file_path))
            
            entry.file_path = file_path
        
        # Update entry
        entry.type = form.type.data
        entry.category = form.category.data
        entry.amount = form.amount.data
        entry.description = form.description.data
        entry.date = form.date.data
        entry.invoice_number = form.invoice_number.data
        entry.payment_method = form.payment_method.data
        
        # Update optional relationships
        if form.client_id.data != 0:
            entry.client_id = form.client_id.data
        else:
            entry.client_id = None
            
        if form.supplier_id.data != 0:
            entry.supplier_id = form.supplier_id.data
        else:
            entry.supplier_id = None
            
        if form.service_order_id.data != 0:
            entry.service_order_id = form.service_order_id.data
        else:
            entry.service_order_id = None
            
        if form.project_id.data != 0:
            entry.project_id = form.project_id.data
        else:
            entry.project_id = None
        
        db.session.commit()
        
        flash('Lançamento financeiro atualizado com sucesso!', 'success')
        return redirect(url_for('finance.index'))
    
    return render_template('finance/edit.html', form=form, entry=entry)

@finance_bp.route('/<int:entry_id>/delete', methods=['POST'])
def delete_entry(entry_id):
    if not current_user.can_delete():
        flash('Você não tem permissão para excluir lançamentos financeiros.', 'danger')
        return redirect(url_for('finance.index'))
    
    entry = FinancialEntry.query.get_or_404(entry_id)
    
    # Remove file if exists
    if entry.file_path:
        file_path = os.path.join(current_app.root_path, 'static', entry.file_path)
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.session.delete(entry)
    db.session.commit()
    
    flash('Lançamento financeiro excluído com sucesso!', 'success')
    return redirect(url_for('finance.index'))

@finance_bp.route('/purchases')
def purchases():
    # Get all expense entries
    expenses = FinancialEntry.query.filter_by(type='expense').order_by(FinancialEntry.date.desc()).all()
    
    return render_template('finance/purchases.html', expenses=expenses)

@finance_bp.route('/sales')
def sales():
    # Get all income entries
    incomes = FinancialEntry.query.filter_by(type='income').order_by(FinancialEntry.date.desc()).all()
    
    return render_template('finance/sales.html', incomes=incomes)

@finance_bp.route('/stats')
def stats():
    # Get total income and expense for charts
    total_income = db.session.query(func.sum(FinancialEntry.amount)).filter(FinancialEntry.type == 'income').scalar() or 0
    total_expenses = db.session.query(func.sum(FinancialEntry.amount)).filter(FinancialEntry.type == 'expense').scalar() or 0
    
    return jsonify({
        'total_income': float(total_income),
        'total_expenses': float(total_expenses)
    })

@finance_bp.route('/category-stats')
def category_stats():
    # Get top categories and their amounts
    entries = db.session.query(
        FinancialEntry.category,
        func.sum(FinancialEntry.amount).label('total'),
        FinancialEntry.type
    ).group_by(FinancialEntry.category, FinancialEntry.type).order_by(func.sum(FinancialEntry.amount).desc()).limit(10).all()
    
    categories = [entry.category for entry in entries]
    amounts = [float(entry.total) for entry in entries]
    types = [entry.type for entry in entries]
    
    return jsonify({
        'categories': categories,
        'amounts': amounts,
        'types': types
    })
