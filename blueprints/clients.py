from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from models import Client, Supplier, ServiceOrder, Project, FinancialEntry
from forms import ClientForm, SupplierForm, SearchForm

clients_bp = Blueprint('clients', __name__, url_prefix='/clients')

# Clients Routes
@clients_bp.route('/')
@login_required
def index():
    search_form = SearchForm()
    
    # Query based on search parameters if any
    query = Client.query
    
    if request.args.get('query'):
        search_term = f"%{request.args.get('query')}%"
        query = query.filter(Client.name.like(search_term) | 
                            Client.email.like(search_term) |
                            Client.contact_person.like(search_term))
    
    # Get all clients
    clients = query.order_by(Client.name).all()
    
    return render_template('clients/index.html', 
                          clients=clients, 
                          search_form=search_form)

@clients_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_client():
    form = ClientForm()
    
    if form.validate_on_submit():
        client = Client(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            contact_person=form.contact_person.data,
            active=form.active.data
        )
        
        db.session.add(client)
        db.session.commit()
        
        flash('Cliente criado com sucesso!', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/create.html', form=form)

@clients_bp.route('/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    form = ClientForm(obj=client)
    
    if form.validate_on_submit():
        client.name = form.name.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.address = form.address.data
        client.city = form.city.data
        client.state = form.state.data
        client.zip_code = form.zip_code.data
        client.contact_person = form.contact_person.data
        client.active = form.active.data
        
        db.session.commit()
        
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('clients.index'))
    
    return render_template('clients/edit.html', form=form, client=client)

@clients_bp.route('/<int:client_id>/delete', methods=['POST'])
@login_required
def delete_client(client_id):
    if not current_user.can_delete():
        flash('Você não tem permissão para excluir clientes.', 'danger')
        return redirect(url_for('clients.index'))
    
    client = Client.query.get_or_404(client_id)
    
    # Check if client has related records
    if client.service_orders or client.projects or client.financial_entries:
        flash('Não é possível excluir este cliente porque existem registros associados a ele.', 'danger')
        return redirect(url_for('clients.index'))
    
    db.session.delete(client)
    db.session.commit()
    
    flash('Cliente excluído com sucesso!', 'success')
    return redirect(url_for('clients.index'))

@clients_bp.route('/<int:client_id>')
@login_required
def view_client(client_id):
    client = Client.query.get_or_404(client_id)
    
    # Get client service orders
    service_orders = ServiceOrder.query.filter_by(client_id=client_id).order_by(ServiceOrder.created_at.desc()).all()
    
    # Get client projects
    projects = Project.query.filter_by(client_id=client_id).order_by(Project.created_at.desc()).all()
    
    # Get client financial entries if user has access
    financial_entries = None
    if current_user.has_finance_access():
        financial_entries = FinancialEntry.query.filter_by(client_id=client_id).order_by(FinancialEntry.date.desc()).all()
    
    return render_template('clients/view.html', 
                          client=client,
                          service_orders=service_orders,
                          projects=projects,
                          financial_entries=financial_entries)

# Suppliers Routes
@clients_bp.route('/suppliers')
@login_required
def suppliers():
    search_form = SearchForm()
    
    # Query based on search parameters
    query = Supplier.query
    
    if request.args.get('query'):
        search_term = f"%{request.args.get('query')}%"
        query = query.filter(
            Supplier.name.like(search_term) | 
            Supplier.email.like(search_term) |
            Supplier.phone.like(search_term)
        )
    
    # Get only active suppliers by default
    if not request.args.get('show_inactive'):
        query = query.filter_by(active=True)
        
    suppliers = query.order_by(Supplier.name).all()
    return render_template('clients/suppliers.html', 
                         suppliers=suppliers,
                         search_form=search_form)

@clients_bp.route('/suppliers/create', methods=['GET', 'POST'])
@login_required
def create_supplier():
    form = SupplierForm()
    
    if form.validate_on_submit():
        supplier = Supplier(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            city=form.city.data,
            state=form.state.data,
            zip_code=form.zip_code.data,
            contact_person=form.contact_person.data
        )
        db.session.add(supplier)
        db.session.commit()
        
        flash('Fornecedor criado com sucesso!', 'success')
        return redirect(url_for('clients.suppliers'))
        
    return render_template('clients/create_supplier.html', form=form)

@clients_bp.route('/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    form = SupplierForm(obj=supplier)
    
    if form.validate_on_submit():
        supplier.name = form.name.data
        supplier.email = form.email.data
        supplier.phone = form.phone.data
        supplier.address = form.address.data
        supplier.city = form.city.data
        supplier.state = form.state.data
        supplier.zip_code = form.zip_code.data
        supplier.contact_person = form.contact_person.data
        
        db.session.commit()
        flash('Fornecedor atualizado com sucesso!', 'success')
        return redirect(url_for('clients.suppliers'))
        
    return render_template('clients/edit_supplier.html', form=form, supplier=supplier)

@clients_bp.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    if not current_user.can_delete():
        flash('Você não tem permissão para excluir fornecedores.', 'danger')
        return redirect(url_for('clients.suppliers'))
        
    supplier = Supplier.query.get_or_404(supplier_id)
    supplier.active = False
    db.session.commit()
    
    flash('Fornecedor excluído com sucesso!', 'success')
    return redirect(url_for('clients.suppliers'))


@clients_bp.route('/suppliers/<int:supplier_id>')
@login_required
def view_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Get supplier inventory items
    inventory_items = supplier.inventory_items
    
    # Get supplier financial entries if user has access
    financial_entries = None
    if current_user.has_finance_access():
        financial_entries = FinancialEntry.query.filter_by(supplier_id=supplier_id).order_by(FinancialEntry.date.desc()).all()
    
    return render_template('clients/view_supplier.html', 
                          supplier=supplier,
                          inventory_items=inventory_items,
                          financial_entries=financial_entries)
