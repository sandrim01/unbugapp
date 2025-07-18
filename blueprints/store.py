
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import StoreItem, Supplier
from forms import StoreItemForm, SearchForm
from datetime import datetime

store_bp = Blueprint('store', __name__, url_prefix='/store')

@store_bp.route('/')
@login_required
def index():
    categories = db.session.query(StoreItem.category).distinct().all()
    category_items = {}
    
    for category in categories:
        category_items[category[0]] = StoreItem.query.filter_by(category=category[0]).all()
    
    return render_template('store/index.html', category_items=category_items)

@store_bp.route('/manage')
@login_required
def manage():
    search_form = SearchForm()
    query = StoreItem.query
    
    if request.args.get('query'):
        search_term = f"%{request.args.get('query')}%"
        query = query.filter(StoreItem.name.like(search_term) | 
                           StoreItem.sku.like(search_term) |
                           StoreItem.category.like(search_term))

    items = query.order_by(StoreItem.name).all()
    return render_template('store/manage.html', items=items, search_form=search_form)

@store_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_item():
    form = StoreItemForm()
    form.supplier_id.choices = [(0, 'Nenhum')] + [(s.id, s.name) for s in Supplier.query.filter_by(active=True).all()]
    
    if form.validate_on_submit():
        if StoreItem.query.filter_by(sku=form.sku.data).first():
            flash('Já existe um item com este SKU.', 'danger')
            return render_template('store/create.html', form=form)

        item = StoreItem(
            name=form.name.data,
            description=form.description.data,
            sku=form.sku.data,
            category=form.category.data,
            quantity=form.quantity.data,
            minimum_stock=form.minimum_stock.data,
            unit_price=form.unit_price.data,
            location=form.location.data,
            supplier_id=form.supplier_id.data if form.supplier_id.data != 0 else None
        )
        
        db.session.add(item)
        db.session.commit()
        flash('Item adicionado com sucesso!', 'success')
        return redirect(url_for('store.manage'))
        
    return render_template('store/create.html', form=form)
