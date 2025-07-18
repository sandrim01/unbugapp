from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import datetime, timedelta
from models import ServiceOrder, Project, StockItem, StoreItem, FinancialEntry
from app import db

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
@login_required
def index():
    # Fetch dashboard data
    open_orders = ServiceOrder.query.filter(ServiceOrder.status.in_(['open', 'in_progress'])).count()
    active_projects = Project.query.filter(Project.status.in_(['planning', 'in_progress'])).count()
    
    # Financial summary - only for management and admin roles
    financial_summary = None
    if current_user.has_finance_access():
        income = db.session.query(func.sum(FinancialEntry.amount)).filter_by(type='income').scalar() or 0
        expenses = db.session.query(func.sum(FinancialEntry.amount)).filter_by(type='expense').scalar() or 0
        financial_summary = {
            'income': income,
            'expenses': expenses,
            'balance': income - expenses
        }
    
    # Low stock items
    low_stock_items = StockItem.query.filter(StockItem.quantity <= StockItem.minimum_stock).count()
    
    # Recent service orders
    recent_orders = ServiceOrder.query.order_by(ServiceOrder.created_at.desc()).limit(5).all()
    
    # Recent projects
    recent_projects = Project.query.order_by(Project.created_at.desc()).limit(5).all()
    
    return render_template('dashboard/index.html', 
                          open_orders=open_orders,
                          active_projects=active_projects,
                          financial_summary=financial_summary,
                          low_stock_items=low_stock_items,
                          recent_orders=recent_orders,
                          recent_projects=recent_projects)

@dashboard_bp.route('/service-order-stats')
@login_required
def service_order_stats():
    # Get counts of service orders by status
    open_count = ServiceOrder.query.filter_by(status='open').count()
    in_progress_count = ServiceOrder.query.filter_by(status='in_progress').count()
    completed_count = ServiceOrder.query.filter_by(status='completed').count()
    cancelled_count = ServiceOrder.query.filter_by(status='cancelled').count()
    
    # Return the data as JSON
    return jsonify({
        'open': open_count,
        'in_progress': in_progress_count,
        'completed': completed_count,
        'cancelled': cancelled_count
    })

@dashboard_bp.route('/project-stats')
@login_required
def project_stats():
    # Get counts of projects by status
    planning_count = Project.query.filter_by(status='planning').count()
    in_progress_count = Project.query.filter_by(status='in_progress').count()
    on_hold_count = Project.query.filter_by(status='on_hold').count()
    completed_count = Project.query.filter_by(status='completed').count()
    cancelled_count = Project.query.filter_by(status='cancelled').count()
    
    # Return the data as JSON
    return jsonify({
        'planning': planning_count,
        'in_progress': in_progress_count,
        'on_hold': on_hold_count,
        'completed': completed_count,
        'cancelled': cancelled_count
    })

@dashboard_bp.route('/finance-stats')
@login_required
def finance_stats():
    # Only allow access to users with finance permissions
    if not current_user.has_finance_access():
        return jsonify({'error': 'Permission denied'}), 403
    
    # Get the past 6 months of financial data
    today = datetime.utcnow()
    six_months_ago = today - timedelta(days=180)
    months = []
    income_data = []
    expense_data = []
    
    # Generate dates for the past 6 months
    for i in range(6):
        month_date = today - timedelta(days=30 * i)
        month_name = month_date.strftime('%b/%Y')
        months.insert(0, month_name)
        
        # Calculate month boundaries for query
        month_start = datetime(month_date.year, month_date.month, 1)
        next_month = month_date.month % 12 + 1
        year = month_date.year + (1 if next_month == 1 else 0)
        month_end = datetime(year, next_month, 1) - timedelta(days=1)
        
        # Query income and expenses for the month
        month_income = db.session.query(func.sum(FinancialEntry.amount)) \
            .filter(FinancialEntry.type == 'income',
                    FinancialEntry.date >= month_start,
                    FinancialEntry.date <= month_end) \
            .scalar() or 0
            
        month_expenses = db.session.query(func.sum(FinancialEntry.amount)) \
            .filter(FinancialEntry.type == 'expense',
                    FinancialEntry.date >= month_start,
                    FinancialEntry.date <= month_end) \
            .scalar() or 0
            
        income_data.insert(0, float(month_income))
        expense_data.insert(0, float(month_expenses))
    
    # Return the data as JSON
    return jsonify({
        'months': months,
        'income': income_data,
        'expenses': expense_data
    })
