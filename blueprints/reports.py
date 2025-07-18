
from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from datetime import datetime, timedelta
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from fpdf import FPDF
import os
from app import db
from models import ServiceOrder, Project, FinancialEntry, StockItem, Client, Supplier, Employee
from sqlalchemy import func, desc

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.before_request
@login_required
def check_reports_access():
    # Verificar se o usuário tem acesso ao módulo de relatórios
    if not current_user.is_management():
        flash('Você não tem permissão para acessar o módulo de relatórios.', 'danger')
        return redirect(url_for('dashboard.index'))

@reports_bp.route('/')
def index():
    return render_template('reports/index.html')

@reports_bp.route('/finance')
def finance():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Converter strings para objetos datetime
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Consulta para receitas
    income = FinancialEntry.query.filter(
        FinancialEntry.type == 'income',
        FinancialEntry.date >= start_date_obj,
        FinancialEntry.date <= end_date_obj
    ).all()
    
    # Consulta para despesas
    expenses = FinancialEntry.query.filter(
        FinancialEntry.type == 'expense',
        FinancialEntry.date >= start_date_obj,
        FinancialEntry.date <= end_date_obj
    ).all()
    
    # Cálculos totais
    total_income = sum(float(entry.amount) for entry in income)
    total_expenses = sum(float(entry.amount) for entry in expenses)
    balance = total_income - total_expenses
    
    # Categorias
    income_by_category = db.session.query(
        FinancialEntry.category, 
        func.sum(FinancialEntry.amount).label('total')
    ).filter(
        FinancialEntry.type == 'income',
        FinancialEntry.date >= start_date_obj,
        FinancialEntry.date <= end_date_obj
    ).group_by(FinancialEntry.category).all()
    
    expense_by_category = db.session.query(
        FinancialEntry.category, 
        func.sum(FinancialEntry.amount).label('total')
    ).filter(
        FinancialEntry.type == 'expense',
        FinancialEntry.date >= start_date_obj,
        FinancialEntry.date <= end_date_obj
    ).group_by(FinancialEntry.category).all()
    
    return render_template(
        'reports/finance.html',
        income=income,
        expenses=expenses,
        total_income=total_income,
        total_expenses=total_expenses,
        balance=balance,
        income_by_category=income_by_category,
        expense_by_category=expense_by_category,
        start_date=start_date,
        end_date=end_date
    )

@reports_bp.route('/orders')
def orders():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    status = request.args.get('status', '')
    
    # Converter strings para objetos datetime
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Consulta base
    query = ServiceOrder.query.filter(
        ServiceOrder.start_date >= start_date_obj,
        ServiceOrder.start_date <= end_date_obj
    )
    
    # Filtrar por status se fornecido
    if status:
        query = query.filter(ServiceOrder.status == status)
    
    # Obter ordens de serviço
    orders = query.order_by(ServiceOrder.start_date.desc()).all()
    
    # Estatísticas
    total_orders = len(orders)
    status_counts = {
        'open': sum(1 for order in orders if order.status == 'open'),
        'in_progress': sum(1 for order in orders if order.status == 'in_progress'),
        'completed': sum(1 for order in orders if order.status == 'completed'),
        'cancelled': sum(1 for order in orders if order.status == 'cancelled')
    }
    
    # Ordens por cliente
    client_orders = db.session.query(
        Client.name, 
        func.count(ServiceOrder.id).label('count')
    ).join(
        ServiceOrder, 
        ServiceOrder.client_id == Client.id
    ).filter(
        ServiceOrder.start_date >= start_date_obj,
        ServiceOrder.start_date <= end_date_obj
    ).group_by(Client.name).order_by(desc('count')).limit(10).all()
    
    return render_template(
        'reports/orders.html',
        orders=orders,
        total_orders=total_orders,
        status_counts=status_counts,
        client_orders=client_orders,
        start_date=start_date,
        end_date=end_date,
        status=status
    )

@reports_bp.route('/projects')
def projects():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    status = request.args.get('status', '')
    
    # Converter strings para objetos datetime
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Consulta base
    query = Project.query.filter(
        Project.start_date >= start_date_obj,
        Project.start_date <= end_date_obj
    )
    
    # Filtrar por status se fornecido
    if status:
        query = query.filter(Project.status == status)
    
    # Obter projetos
    projects = query.order_by(Project.start_date.desc()).all()
    
    # Estatísticas
    total_projects = len(projects)
    status_counts = {
        'planning': sum(1 for project in projects if project.status == 'planning'),
        'in_progress': sum(1 for project in projects if project.status == 'in_progress'),
        'on_hold': sum(1 for project in projects if project.status == 'on_hold'),
        'completed': sum(1 for project in projects if project.status == 'completed'),
        'cancelled': sum(1 for project in projects if project.status == 'cancelled')
    }
    
    # Projetos por cliente
    client_projects = db.session.query(
        Client.name, 
        func.count(Project.id).label('count')
    ).join(
        Project, 
        Project.client_id == Client.id
    ).filter(
        Project.start_date >= start_date_obj,
        Project.start_date <= end_date_obj
    ).group_by(Client.name).order_by(desc('count')).limit(10).all()
    
    # Total de orçamento
    total_budget = sum(float(project.budget or 0) for project in projects)
    
    return render_template(
        'reports/projects.html',
        projects=projects,
        total_projects=total_projects,
        status_counts=status_counts,
        client_projects=client_projects,
        total_budget=total_budget,
        start_date=start_date,
        end_date=end_date,
        status=status
    )

@reports_bp.route('/stock')
def stock():
    category = request.args.get('category', '')
    low_stock_only = request.args.get('low_stock', 'false') == 'true'
    
    # Consulta base
    query = StockItem.query
    
    # Filtrar por categoria
    if category:
        query = query.filter(StockItem.category == category)
    
    # Filtrar por estoque baixo
    if low_stock_only:
        query = query.filter(StockItem.quantity <= StockItem.minimum_stock)
    
    # Obter itens
    items = query.order_by(StockItem.name).all()
    
    # Obter todas as categorias para o filtro
    categories = db.session.query(StockItem.category).distinct().all()
    
    # Estatísticas
    total_items = len(items)
    total_value = sum(float(item.unit_price or 0) * item.quantity for item in items)
    low_stock_count = sum(1 for item in items if item.is_low_stock())
    
    # Itens por categoria
    category_counts = db.session.query(
        StockItem.category, 
        func.count(StockItem.id).label('count')
    ).group_by(StockItem.category).all()
    
    return render_template(
        'reports/stock.html',
        items=items,
        total_items=total_items,
        total_value=total_value,
        low_stock_count=low_stock_count,
        category_counts=category_counts,
        categories=[cat[0] for cat in categories],
        selected_category=category,
        low_stock_only=low_stock_only
    )

@reports_bp.route('/clients')
def clients():
    is_active = request.args.get('active', 'all')
    
    # Consulta base
    query = Client.query
    
    # Filtrar por status
    if is_active == 'active':
        query = query.filter(Client.active == True)
    elif is_active == 'inactive':
        query = query.filter(Client.active == False)
    
    # Obter clientes
    clients = query.order_by(Client.name).all()
    
    # Estatísticas
    total_clients = len(clients)
    active_clients = sum(1 for client in clients if client.active)
    
    # Clientes por cidade/estado
    city_counts = {}
    state_counts = {}
    
    for client in clients:
        if client.city:
            city_counts[client.city] = city_counts.get(client.city, 0) + 1
        if client.state:
            state_counts[client.state] = state_counts.get(client.state, 0) + 1
    
    # Top clientes por projetos
    top_project_clients = db.session.query(
        Client.name, 
        func.count(Project.id).label('count')
    ).join(
        Project, 
        Project.client_id == Client.id
    ).group_by(Client.name).order_by(desc('count')).limit(10).all()
    
    # Top clientes por ordens de serviço
    top_order_clients = db.session.query(
        Client.name, 
        func.count(ServiceOrder.id).label('count')
    ).join(
        ServiceOrder, 
        ServiceOrder.client_id == Client.id
    ).group_by(Client.name).order_by(desc('count')).limit(10).all()
    
    return render_template(
        'reports/clients.html',
        clients=clients,
        total_clients=total_clients,
        active_clients=active_clients,
        inactive_clients=total_clients - active_clients,
        city_counts=city_counts,
        state_counts=state_counts,
        top_project_clients=top_project_clients,
        top_order_clients=top_order_clients,
        active_filter=is_active
    )

@reports_bp.route('/export/finance')
def export_finance():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    export_format = request.args.get('format', 'excel')

    if export_format == 'pdf':
        # Criar PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(190, 10, 'Relatório Financeiro', 0, 1, 'C')
        pdf.ln(10)

        # Adicionar período
        pdf.set_font('Arial', '', 12)
        pdf.cell(190, 10, f'Período: {start_date} a {end_date}', 0, 1, 'L')
        
        # Buscar dados
        entries = FinancialEntry.query.filter(
            FinancialEntry.date >= datetime.strptime(start_date, '%Y-%m-%d'),
            FinancialEntry.date <= datetime.strptime(end_date, '%Y-%m-%d')
        ).order_by(FinancialEntry.date).all()

        # Cabeçalho da tabela
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(30, 7, 'Data', 1)
        pdf.cell(30, 7, 'Tipo', 1)
        pdf.cell(40, 7, 'Categoria', 1)
        pdf.cell(30, 7, 'Valor', 1)
        pdf.cell(60, 7, 'Descrição', 1)
        pdf.ln()

        # Dados da tabela
        pdf.set_font('Arial', '', 10)
        for entry in entries:
            pdf.cell(30, 6, entry.date.strftime('%d/%m/%Y'), 1)
            pdf.cell(30, 6, 'Receita' if entry.type == 'income' else 'Despesa', 1)
            pdf.cell(40, 6, entry.category, 1)
            pdf.cell(30, 6, f'R$ {float(entry.amount):.2f}', 1)
            pdf.cell(60, 6, entry.description[:30], 1)
            pdf.ln()

        # Criar buffer para o PDF
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)

        return send_file(
            pdf_output,
            as_attachment=True,
            download_name=f"relatorio_financeiro_{start_date}_{end_date}.pdf",
            mimetype='application/pdf'
        )
    
    # Converter strings para objetos datetime
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Consulta para todas as entradas financeiras no período
    entries = FinancialEntry.query.filter(
        FinancialEntry.date >= start_date_obj,
        FinancialEntry.date <= end_date_obj
    ).order_by(FinancialEntry.date).all()
    
    # Criar DataFrame com pandas
    data = []
    for entry in entries:
        client_name = entry.client.name if entry.client else None
        supplier_name = entry.supplier.name if entry.supplier else None
        
        data.append({
            'Data': entry.date.strftime('%d/%m/%Y'),
            'Tipo': 'Receita' if entry.type == 'income' else 'Despesa',
            'Categoria': entry.category,
            'Valor': float(entry.amount),
            'Descrição': entry.description,
            'Cliente': client_name,
            'Fornecedor': supplier_name,
            'Método de Pagamento': entry.payment_method
        })
    
    df = pd.DataFrame(data)
    
    # Criar buffer para o arquivo Excel
    output = BytesIO()
    
    # Criar um objeto ExcelWriter
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Escrever o DataFrame principal
        df.to_excel(writer, sheet_name='Lançamentos', index=False)
        
        # Criar uma folha de resumo
        summary_data = {
            'Métrica': [
                'Total de Receitas', 
                'Total de Despesas', 
                'Saldo',
                'Período do Relatório'
            ],
            'Valor': [
                sum(entry.amount for entry in entries if entry.type == 'income'),
                sum(entry.amount for entry in entries if entry.type == 'expense'),
                sum(entry.amount if entry.type == 'income' else -float(entry.amount) for entry in entries),
                f"{start_date} a {end_date}"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Resumo', index=False)
        
        # Adicionar folha para categorias
        income_by_category = {}
        expense_by_category = {}
        
        for entry in entries:
            if entry.type == 'income':
                income_by_category[entry.category] = income_by_category.get(entry.category, 0) + float(entry.amount)
            else:
                expense_by_category[entry.category] = expense_by_category.get(entry.category, 0) + float(entry.amount)
        
        categories_data = []
        for category, amount in income_by_category.items():
            categories_data.append({
                'Categoria': category,
                'Tipo': 'Receita',
                'Valor': amount
            })
        
        for category, amount in expense_by_category.items():
            categories_data.append({
                'Categoria': category,
                'Tipo': 'Despesa',
                'Valor': amount
            })
        
        categories_df = pd.DataFrame(categories_data)
        categories_df.to_excel(writer, sheet_name='Categorias', index=False)
    
    # Posicionar o ponteiro no início do buffer
    output.seek(0)
    
    # Criar nome do arquivo
    filename = f"relatorio_financeiro_{start_date}_{end_date}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@reports_bp.route('/export/orders')
def export_orders():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    status = request.args.get('status', '')
    
    # Converter strings para objetos datetime
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Consulta base
    query = ServiceOrder.query.filter(
        ServiceOrder.start_date >= start_date_obj,
        ServiceOrder.start_date <= end_date_obj
    )
    
    # Filtrar por status se fornecido
    if status:
        query = query.filter(ServiceOrder.status == status)
    
    # Obter ordens de serviço
    orders = query.order_by(ServiceOrder.start_date.desc()).all()
    
    # Criar DataFrame com pandas
    data = []
    for order in orders:
        completion_date = order.completion_date.strftime('%d/%m/%Y') if order.completion_date else 'Não concluído'
        
        data.append({
            'ID': order.id,
            'Título': order.title,
            'Cliente': order.client.name if order.client else 'N/A',
            'Funcionário': order.employee.full_name if order.employee else 'N/A',
            'Status': order.status,
            'Prioridade': order.priority,
            'Data de Início': order.start_date.strftime('%d/%m/%Y'),
            'Data de Conclusão': completion_date,
            'Descrição': order.description
        })
    
    df = pd.DataFrame(data)
    
    # Criar buffer para o arquivo Excel
    output = BytesIO()
    
    # Criar um objeto ExcelWriter
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Escrever o DataFrame principal
        df.to_excel(writer, sheet_name='Ordens de Serviço', index=False)
        
        # Criar uma folha de resumo
        status_counts = {
            'open': sum(1 for order in orders if order.status == 'open'),
            'in_progress': sum(1 for order in orders if order.status == 'in_progress'),
            'completed': sum(1 for order in orders if order.status == 'completed'),
            'cancelled': sum(1 for order in orders if order.status == 'cancelled')
        }
        
        summary_data = {
            'Métrica': [
                'Total de Ordens', 
                'Ordens Abertas', 
                'Ordens em Progresso',
                'Ordens Concluídas',
                'Ordens Canceladas',
                'Período do Relatório'
            ],
            'Valor': [
                len(orders),
                status_counts['open'],
                status_counts['in_progress'],
                status_counts['completed'],
                status_counts['cancelled'],
                f"{start_date} a {end_date}"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Resumo', index=False)
    
    # Posicionar o ponteiro no início do buffer
    output.seek(0)
    
    # Criar nome do arquivo
    status_suffix = f"_{status}" if status else ""
    filename = f"relatorio_ordens{status_suffix}_{start_date}_{end_date}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@reports_bp.route('/export/projects')
def export_projects():
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    status = request.args.get('status', '')
    
    # Converter strings para objetos datetime
    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Consulta base
    query = Project.query.filter(
        Project.start_date >= start_date_obj,
        Project.start_date <= end_date_obj
    )
    
    # Filtrar por status se fornecido
    if status:
        query = query.filter(Project.status == status)
    
    # Obter projetos
    projects = query.order_by(Project.start_date.desc()).all()
    
    # Criar DataFrame com pandas
    data = []
    for project in projects:
        end_date = project.end_date.strftime('%d/%m/%Y') if project.end_date else 'Não definido'
        
        data.append({
            'ID': project.id,
            'Nome': project.name,
            'Cliente': project.client.name if project.client else 'N/A',
            'Gerente': project.manager.full_name if project.manager else 'N/A',
            'Status': project.status,
            'Data de Início': project.start_date.strftime('%d/%m/%Y') if project.start_date else 'Não definido',
            'Data de Término': end_date,
            'Orçamento': float(project.budget) if project.budget else 0,
            'Descrição': project.description
        })
    
    df = pd.DataFrame(data)
    
    # Criar buffer para o arquivo Excel
    output = BytesIO()
    
    # Criar um objeto ExcelWriter
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Escrever o DataFrame principal
        df.to_excel(writer, sheet_name='Projetos', index=False)
        
        # Criar uma folha de resumo
        status_counts = {
            'planning': sum(1 for project in projects if project.status == 'planning'),
            'in_progress': sum(1 for project in projects if project.status == 'in_progress'),
            'on_hold': sum(1 for project in projects if project.status == 'on_hold'),
            'completed': sum(1 for project in projects if project.status == 'completed'),
            'cancelled': sum(1 for project in projects if project.status == 'cancelled')
        }
        
        summary_data = {
            'Métrica': [
                'Total de Projetos', 
                'Projetos em Planejamento', 
                'Projetos em Progresso',
                'Projetos em Espera',
                'Projetos Concluídos',
                'Projetos Cancelados',
                'Orçamento Total',
                'Período do Relatório'
            ],
            'Valor': [
                len(projects),
                status_counts['planning'],
                status_counts['in_progress'],
                status_counts['on_hold'],
                status_counts['completed'],
                status_counts['cancelled'],
                sum(float(project.budget or 0) for project in projects),
                f"{start_date} a {end_date}"
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Resumo', index=False)
    
    # Posicionar o ponteiro no início do buffer
    output.seek(0)
    
    # Criar nome do arquivo
    status_suffix = f"_{status}" if status else ""
    filename = f"relatorio_projetos{status_suffix}_{start_date}_{end_date}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@reports_bp.route('/export/stock')
def export_stock():
    category = request.args.get('category', '')
    low_stock_only = request.args.get('low_stock', 'false') == 'true'
    
    # Consulta base
    query = StockItem.query
    
    # Filtrar por categoria
    if category:
        query = query.filter(StockItem.category == category)
    
    # Filtrar por estoque baixo
    if low_stock_only:
        query = query.filter(StockItem.quantity <= StockItem.minimum_stock)
    
    # Obter itens
    items = query.order_by(StockItem.name).all()
    
    # Criar DataFrame com pandas
    data = []
    for item in items:
        data.append({
            'ID': item.id,
            'Nome': item.name,
            'SKU': item.sku,
            'Categoria': item.category,
            'Quantidade': item.quantity,
            'Estoque Mínimo': item.minimum_stock,
            'Preço Unitário': float(item.unit_price) if item.unit_price else 0,
            'Valor Total': float(item.unit_price) * item.quantity if item.unit_price else 0,
            'Localização': item.location,
            'Fornecedor': item.supplier.name if item.supplier else 'N/A',
            'Status': 'Estoque Baixo' if item.is_low_stock() else 'Normal'
        })
    
    df = pd.DataFrame(data)
    
    # Criar buffer para o arquivo Excel
    output = BytesIO()
    
    # Criar um objeto ExcelWriter
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Escrever o DataFrame principal
        df.to_excel(writer, sheet_name='Estoque', index=False)
        
        # Criar uma folha de resumo
        summary_data = {
            'Métrica': [
                'Total de Itens', 
                'Itens com Estoque Baixo', 
                'Valor Total do Estoque',
                'Categoria Filtrada',
                'Filtro de Estoque Baixo'
            ],
            'Valor': [
                len(items),
                sum(1 for item in items if item.is_low_stock()),
                sum(float(item.unit_price or 0) * item.quantity for item in items),
                category if category else 'Todas',
                'Sim' if low_stock_only else 'Não'
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Resumo', index=False)
        
        # Adicionar folha para categorias
        category_data = []
        categories = {}
        
        for item in items:
            if item.category in categories:
                categories[item.category]['count'] += 1
                categories[item.category]['value'] += float(item.unit_price or 0) * item.quantity
            else:
                categories[item.category] = {
                    'count': 1,
                    'value': float(item.unit_price or 0) * item.quantity
                }
        
        for category, data in categories.items():
            category_data.append({
                'Categoria': category,
                'Quantidade de Itens': data['count'],
                'Valor Total': data['value']
            })
        
        category_df = pd.DataFrame(category_data)
        category_df.to_excel(writer, sheet_name='Categorias', index=False)
    
    # Posicionar o ponteiro no início do buffer
    output.seek(0)
    
    # Criar nome do arquivo
    category_suffix = f"_{category}" if category else ""
    low_stock_suffix = "_baixo_estoque" if low_stock_only else ""
    filename = f"relatorio_estoque{category_suffix}{low_stock_suffix}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@reports_bp.route('/export/clients')
def export_clients():
    is_active = request.args.get('active', 'all')
    
    # Consulta base
    query = Client.query
    
    # Filtrar por status
    if is_active == 'active':
        query = query.filter(Client.active == True)
    elif is_active == 'inactive':
        query = query.filter(Client.active == False)
    
    # Obter clientes
    clients = query.order_by(Client.name).all()
    
    # Criar DataFrame com pandas
    data = []
    for client in clients:
        # Contar ordens e projetos para cada cliente
        order_count = len(client.service_orders)
        project_count = len(client.projects)
        
        data.append({
            'ID': client.id,
            'Nome': client.name,
            'Email': client.email,
            'Telefone': client.phone,
            'Contato': client.contact_person,
            'Cidade': client.city,
            'Estado': client.state,
            'CEP': client.zip_code,
            'Status': 'Ativo' if client.active else 'Inativo',
            'Ordens de Serviço': order_count,
            'Projetos': project_count
        })
    
    df = pd.DataFrame(data)
    
    # Criar buffer para o arquivo Excel
    output = BytesIO()
    
    # Criar um objeto ExcelWriter
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Escrever o DataFrame principal
        df.to_excel(writer, sheet_name='Clientes', index=False)
        
        # Criar uma folha de resumo
        summary_data = {
            'Métrica': [
                'Total de Clientes', 
                'Clientes Ativos', 
                'Clientes Inativos',
                'Filtro Aplicado'
            ],
            'Valor': [
                len(clients),
                sum(1 for client in clients if client.active),
                sum(1 for client in clients if not client.active),
                {'all': 'Todos', 'active': 'Apenas Ativos', 'inactive': 'Apenas Inativos'}[is_active]
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Resumo', index=False)
        
        # Adicionar folha para distribuição geográfica
        geo_data = []
        cities = {}
        states = {}
        
        for client in clients:
            if client.city:
                cities[client.city] = cities.get(client.city, 0) + 1
            if client.state:
                states[client.state] = states.get(client.state, 0) + 1
        
        # Adicionar dados de cidades
        for city, count in cities.items():
            geo_data.append({
                'Tipo': 'Cidade',
                'Nome': city,
                'Quantidade': count
            })
        
        # Adicionar dados de estados
        for state, count in states.items():
            geo_data.append({
                'Tipo': 'Estado',
                'Nome': state,
                'Quantidade': count
            })
        
        geo_df = pd.DataFrame(geo_data)
        geo_df.to_excel(writer, sheet_name='Distribuição Geográfica', index=False)
    
    # Posicionar o ponteiro no início do buffer
    output.seek(0)
    
    # Criar nome do arquivo
    active_suffix = f"_{is_active}" if is_active != 'all' else ""
    filename = f"relatorio_clientes{active_suffix}.xlsx"
    
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
