from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_file
import io
from flask_login import login_required, current_user
from app import db
from models import ServiceOrder, Project, Client, Employee, OrderItem, StockItem
from forms import ServiceOrderForm, ProjectForm, OrderItemForm, SearchForm
from datetime import datetime

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

# Service Orders Routes
@orders_bp.route('/')
@login_required
def index():
    search_form = SearchForm()
    
    # Query based on search parameters if any
    query = ServiceOrder.query
    
    if request.args.get('query'):
        search_term = f"%{request.args.get('query')}%"
        query = query.filter(ServiceOrder.title.like(search_term) | 
                             ServiceOrder.description.like(search_term))
    
    if request.args.get('status') and request.args.get('status') != '':
        query = query.filter(ServiceOrder.status == request.args.get('status'))
    
    if request.args.get('date_from'):
        date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        query = query.filter(ServiceOrder.start_date >= date_from)
    
    if request.args.get('date_to'):
        date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
        query = query.filter(ServiceOrder.start_date <= date_to)
    
    # Order by most recent first
    service_orders = query.order_by(ServiceOrder.created_at.desc()).all()
    
    return render_template('orders/index.html', 
                          service_orders=service_orders, 
                          search_form=search_form)

@orders_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_order():
    form = ServiceOrderForm()
    
    # Populate the select fields with available options
    form.client_id.choices = [(client.id, client.name) for client in Client.query.filter_by(active=True).all()]
    form.employee_id.choices = [(emp.id, emp.full_name) for emp in Employee.query.filter_by(active=True).all()]
    
    if form.validate_on_submit():
        service_order = ServiceOrder(
            title=form.title.data,
            description=form.description.data,
            status=form.status.data,
            priority=form.priority.data,
            client_id=form.client_id.data,
            employee_id=form.employee_id.data,
            start_date=form.start_date.data,
            completion_date=form.completion_date.data,
            notes=form.notes.data
        )
        
        db.session.add(service_order)
        db.session.commit()
        
        flash('Ordem de serviço criada com sucesso!', 'success')
        return redirect(url_for('orders.view_order', order_id=service_order.id))
    
    return render_template('orders/create.html', form=form)

@orders_bp.route('/<int:order_id>')
@login_required
def view_order(order_id):
    service_order = ServiceOrder.query.get_or_404(order_id)
    
    # Form for adding items to the order
    form = OrderItemForm()
    form.inventory_item_id.choices = [(item.id, f"{item.name} (Estoque: {item.quantity})") 
                                     for item in StockItem.query.filter(StockItem.quantity > 0).all()]
    form.service_order_id.data = order_id
    
    return render_template('orders/view.html', 
                          service_order=service_order, 
                          form=form)

@orders_bp.route('/<int:order_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_order(order_id):
    service_order = ServiceOrder.query.get_or_404(order_id)
    form = ServiceOrderForm(obj=service_order)
    
    # Populate the select fields with available options
    form.client_id.choices = [(client.id, client.name) for client in Client.query.filter_by(active=True).all()]
    form.employee_id.choices = [(emp.id, emp.full_name) for emp in Employee.query.filter_by(active=True).all()]
    
    if form.validate_on_submit():
        service_order.title = form.title.data
        service_order.description = form.description.data
        service_order.status = form.status.data
        service_order.priority = form.priority.data
        service_order.client_id = form.client_id.data
        service_order.employee_id = form.employee_id.data
        service_order.start_date = form.start_date.data
        service_order.completion_date = form.completion_date.data
        service_order.notes = form.notes.data
        
        db.session.commit()
        
        flash('Ordem de serviço atualizada com sucesso!', 'success')
        return redirect(url_for('orders.view_order', order_id=service_order.id))
    
    return render_template('orders/edit.html', form=form, service_order=service_order)

@orders_bp.route('/<int:order_id>/delete', methods=['POST'])
@login_required
def delete_order(order_id):
    if not current_user.can_delete():
        flash('Você não tem permissão para excluir ordens de serviço.', 'danger')
        return redirect(url_for('orders.index'))
    
    service_order = ServiceOrder.query.get_or_404(order_id)
    
    # Delete associated order items
    OrderItem.query.filter_by(service_order_id=order_id).delete()
    
    db.session.delete(service_order)
    db.session.commit()
    
    flash('Ordem de serviço excluída com sucesso!', 'success')
    return redirect(url_for('orders.index'))

@orders_bp.route('/<int:order_id>/add-item', methods=['POST'])
@login_required
def add_item(order_id):
    service_order = ServiceOrder.query.get_or_404(order_id)
    form = OrderItemForm()
    
    form.inventory_item_id.choices = [(item.id, item.name) for item in InventoryItem.query.all()]
    
    if form.validate_on_submit():
        inventory_item = InventoryItem.query.get(form.inventory_item_id.data)
        
        # Check if quantity is available
        if inventory_item.quantity < form.quantity.data:
            flash(f'Estoque insuficiente. Disponível: {inventory_item.quantity}', 'danger')
            return redirect(url_for('orders.view_order', order_id=order_id))
        
        # Create order item
        order_item = OrderItem(
            service_order_id=order_id,
            inventory_item_id=form.inventory_item_id.data,
            quantity=form.quantity.data
        )
        
        db.session.add(order_item)
        db.session.commit()
        
        flash('Item adicionado com sucesso!', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'Erro no campo {field}: {error}', 'danger')
    
    return redirect(url_for('orders.view_order', order_id=order_id))

@orders_bp.route('/<int:order_id>/remove-item/<int:item_id>', methods=['POST'])
@login_required
def remove_item(order_id, item_id):
    order_item = OrderItem.query.get_or_404(item_id)
    
    # Make sure the item belongs to the specified order
    if order_item.service_order_id != order_id:
        flash('Item inválido.', 'danger')
        return redirect(url_for('orders.view_order', order_id=order_id))
    
    # Return the items to inventory
    inventory_item = InventoryItem.query.get(order_item.inventory_item_id)
    inventory_item.quantity += order_item.quantity
    
    db.session.delete(order_item)
    db.session.commit()
    
    flash('Item removido com sucesso!', 'success')
    return redirect(url_for('orders.view_order', order_id=order_id))

# Projects Routes
from fpdf import FPDF
from flask_mail import Mail, Message

mail = Mail()

def generate_project_pdf(project, include_budget=True):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.image('./static/img/unbug_logo.png', x=10, y=8, w=30)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Unbug Solutions TI', ln=True, align='C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, 'Projetos e Soluções em TI', ln=True, align='C')
    pdf.line(10, 40, 200, 40)
    
    # Project Details
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Detalhes do Projeto', ln=True)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(50, 10, 'Nome:', 0)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, project.name, ln=True)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(50, 10, 'Cliente:', 0)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, project.client.name, ln=True)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(50, 10, 'Gerente:', 0)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, project.manager.full_name, ln=True)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(50, 10, 'Status:', 0)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, project.status, ln=True)
    
    if include_budget and project.budget:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(50, 10, 'Orçamento:', 0)
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 10, f'R$ {project.budget:,.2f}', ln=True)
    
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Descrição:', ln=True)
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 10, project.description)
    
    # Footer
    pdf.set_y(-30)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 10, f'Documento gerado em {datetime.now().strftime("%d/%m/%Y %H:%M")}', ln=True, align='C')
    pdf.cell(0, 10, 'Unbug Solutions TI - Todos os direitos reservados', align='C')
    
    return pdf.output(dest='S')

@orders_bp.route('/projects/budget/<int:project_id>', methods=['POST'])
@login_required
def update_budget(project_id):
    project = Project.query.get_or_404(project_id)
    budget = request.form.get('budget', type=float)
    if budget:
        project.budget = budget
        db.session.commit()
        flash('Orçamento atualizado com sucesso!', 'success')
    return redirect(url_for('orders.projects'))

@orders_bp.route('/projects/pdf/<int:project_id>')
@login_required
def download_project_pdf(project_id):
    project = Project.query.get_or_404(project_id)
    pdf_type = request.args.get('type', 'project')
    include_budget = pdf_type == 'budget'
    pdf_content = generate_project_pdf(project, include_budget)
    return send_file(
        io.BytesIO(pdf_content),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'projeto_{project.id}.pdf'
    )

@orders_bp.route('/projects/send/<int:project_id>', methods=['POST'])
@login_required
def send_project(project_id):
    project = Project.query.get_or_404(project_id)
    recipient = request.form.get('email')
    
    if not recipient:
        flash('Email do destinatário é obrigatório', 'error')
        return redirect(url_for('orders.projects'))
        
    pdf_content = generate_project_pdf(project)
    msg = Message(
        f'Projeto: {project.name}',
        sender='seu-email@unbug.com',
        recipients=[recipient]
    )
    msg.body = f"""
    Prezado cliente,
    
    Segue em anexo o projeto {project.name}.
    
    Atenciosamente,
    Unbug Solutions TI
    """
    msg.attach(f"projeto_{project.id}.pdf", "application/pdf", pdf_content)
    
    mail.send(msg)
    flash('Projeto enviado com sucesso!', 'success')
    return redirect(url_for('orders.projects'))

@orders_bp.route('/projects')
@login_required
def projects():
    search_form = SearchForm()
    
    # Query based on search parameters if any
    query = Project.query
    
    if request.args.get('query'):
        search_term = f"%{request.args.get('query')}%"
        query = query.filter(Project.name.like(search_term) | 
                             Project.description.like(search_term))
    
    if request.args.get('status') and request.args.get('status') != '':
        query = query.filter(Project.status == request.args.get('status'))
    
    if request.args.get('date_from'):
        date_from = datetime.strptime(request.args.get('date_from'), '%Y-%m-%d')
        query = query.filter(Project.start_date >= date_from)
    
    if request.args.get('date_to'):
        date_to = datetime.strptime(request.args.get('date_to'), '%Y-%m-%d')
        query = query.filter(Project.start_date <= date_to)
    
    # Order by most recent first
    projects = query.order_by(Project.created_at.desc()).all()
    
    return render_template('orders/projects.html', 
                          projects=projects, 
                          search_form=search_form)

@orders_bp.route('/projects/create', methods=['GET', 'POST'])
@login_required
def create_project():
    form = ProjectForm()
    
    # Populate the select fields with available options
    form.client_id.choices = [(client.id, client.name) for client in Client.query.filter_by(active=True).all()]
    form.manager_id.choices = [(emp.id, emp.full_name) for emp in Employee.query.filter_by(active=True).all()]
    
    if form.validate_on_submit():
        project = Project(
            name=form.name.data,
            description=form.description.data,
            status=form.status.data,
            client_id=form.client_id.data,
            manager_id=form.manager_id.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            budget=form.budget.data
        )
        
        db.session.add(project)
        db.session.commit()
        
        flash('Projeto criado com sucesso!', 'success')
        return redirect(url_for('orders.projects'))
    
    return render_template('orders/create_project.html', form=form)

@orders_bp.route('/projects/<int:project_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)
    
    # Populate the select fields with available options
    form.client_id.choices = [(client.id, client.name) for client in Client.query.filter_by(active=True).all()]
    form.manager_id.choices = [(emp.id, emp.full_name) for emp in Employee.query.filter_by(active=True).all()]
    
    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        project.status = form.status.data
        project.client_id = form.client_id.data
        project.manager_id = form.manager_id.data
        project.start_date = form.start_date.data
        project.end_date = form.end_date.data
        project.budget = form.budget.data
        
        db.session.commit()
        
        flash('Projeto atualizado com sucesso!', 'success')
        return redirect(url_for('orders.projects'))
    
    return render_template('orders/edit_project.html', form=form, project=project)

@orders_bp.route('/projects/<int:project_id>/delete', methods=['POST'])
@login_required
def delete_project(project_id):
    if not current_user.can_delete():
        flash('Você não tem permissão para excluir projetos.', 'danger')
        return redirect(url_for('orders.projects'))
    
    project = Project.query.get_or_404(project_id)
    
    db.session.delete(project)
    db.session.commit()
    
    flash('Projeto excluído com sucesso!', 'success')
    return redirect(url_for('orders.projects'))

@orders_bp.route('/by-project/<int:project_id>')
@login_required
def orders_by_project(project_id):
    # Get all service orders related to a project (by client)
    project = Project.query.get_or_404(project_id)
    
    orders = ServiceOrder.query.filter_by(client_id=project.client_id).all()
    
    # Format the data for JSON response
    orders_data = [{
        'id': order.id,
        'title': order.title,
        'status': order.status
    } for order in orders]
    
    return jsonify(orders_data)
