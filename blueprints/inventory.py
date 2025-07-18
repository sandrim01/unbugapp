from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import InventoryItem, Supplier, Client, FinancialEntry
from forms import InventoryItemForm, SearchForm
from sqlalchemy import func
from datetime import datetime

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
@login_required
def index():
    search_form = SearchForm()

    # Query based on search parameters if any
    query = InventoryItem.query

    if request.args.get('query'):
        search_term = f"%{request.args.get('query')}%"
        query = query.filter(InventoryItem.name.like(search_term) | 
                            InventoryItem.sku.like(search_term) |
                            InventoryItem.category.like(search_term))

    # Get all inventory items
    items = query.order_by(InventoryItem.name).all()

    # Get low stock items
    low_stock_items = [item for item in items if item.is_low_stock()]

    return render_template('inventory/index.html', 
                          items=items, 
                          low_stock_items=low_stock_items,
                          search_form=search_form)

@inventory_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_item():
    form = InventoryItemForm()

    # Populate supplier select field
    form.supplier_id.choices = [(0, 'Nenhum')] + [(supplier.id, supplier.name) for supplier in Supplier.query.filter_by(active=True).all()]

    if form.validate_on_submit():
        # Check if SKU already exists
        existing_item = InventoryItem.query.filter_by(sku=form.sku.data).first()
        if existing_item:
            flash('Já existe um item com este SKU.', 'danger')
            return render_template('inventory/create.html', form=form)

        # Create new inventory item
        inventory_item = InventoryItem(
            name=form.name.data,
            description=form.description.data,
            sku=form.sku.data,
            category=form.category.data,
            quantity=form.quantity.data,
            minimum_stock=form.minimum_stock.data,
            unit_price=form.unit_price.data,
            location=form.location.data
        )

        # Set supplier if selected
        if form.supplier_id.data != 0:
            inventory_item.supplier_id = form.supplier_id.data

        db.session.add(inventory_item)
        db.session.commit()

        flash('Item de inventário criado com sucesso!', 'success')
        return redirect(url_for('inventory.index'))

    return render_template('inventory/create.html', form=form)

@inventory_bp.route('/<int:item_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    inventory_item = InventoryItem.query.get_or_404(item_id)
    form = InventoryItemForm(obj=inventory_item)

    # Populate supplier select field
    form.supplier_id.choices = [(0, 'Nenhum')] + [(supplier.id, supplier.name) for supplier in Supplier.query.filter_by(active=True).all()]

    # Set current supplier
    if inventory_item.supplier_id:
        form.supplier_id.data = inventory_item.supplier_id
    else:
        form.supplier_id.data = 0

    if form.validate_on_submit():
        # Check if SKU already exists and is not the current item
        existing_item = InventoryItem.query.filter_by(sku=form.sku.data).first()
        if existing_item and existing_item.id != item_id:
            flash('Já existe um item com este SKU.', 'danger')
            return render_template('inventory/edit.html', form=form, item=inventory_item)

        # Update inventory item
        inventory_item.name = form.name.data
        inventory_item.description = form.description.data
        inventory_item.sku = form.sku.data
        inventory_item.category = form.category.data
        inventory_item.quantity = form.quantity.data
        inventory_item.minimum_stock = form.minimum_stock.data
        inventory_item.unit_price = form.unit_price.data
        inventory_item.location = form.location.data

        # Update supplier
        if form.supplier_id.data != 0:
            inventory_item.supplier_id = form.supplier_id.data
        else:
            inventory_item.supplier_id = None

        db.session.commit()

        flash('Item de inventário atualizado com sucesso!', 'success')
        return redirect(url_for('inventory.index'))

    return render_template('inventory/edit.html', form=form, item=inventory_item)

@inventory_bp.route('/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    if not current_user.can_delete():
        flash('Você não tem permissão para excluir itens do inventário.', 'danger')
        return redirect(url_for('inventory.index'))

    inventory_item = InventoryItem.query.get_or_404(item_id)

    db.session.delete(inventory_item)
    db.session.commit()

    flash('Item de inventário excluído com sucesso!', 'success')
    return redirect(url_for('inventory.index'))

@inventory_bp.route('/store')
@login_required
def store():
    # Group inventory items by category for the store view
    categories = db.session.query(InventoryItem.category).distinct().all()
    category_items = {}

    for category in categories:
        category_items[category[0]] = InventoryItem.query.filter_by(category=category[0]).all()

    return render_template('inventory/store.html', category_items=category_items)

@inventory_bp.route('/search-items')
@login_required
def search_items():
    query = request.args.get('query', '')
    if not query:
        return jsonify([])
    
    items = InventoryItem.query.filter(
        (InventoryItem.name.ilike(f'%{query}%')) |
        (InventoryItem.sku.ilike(f'%{query}%'))
    ).all()
    
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'sku': item.sku,
        'quantity': item.quantity,
        'unit_price': float(item.unit_price)
    } for item in items])

@inventory_bp.route('/check-stock/<int:item_id>')
@login_required
def check_stock(item_id):
    item = InventoryItem.query.get_or_404(item_id)

    return jsonify({
        'id': item.id,
        'name': item.name,
        'available': item.quantity,
        'low_stock': item.is_low_stock()
    })

@inventory_bp.route('/pdv')
@login_required
def pdv():
    # Get active clients for the payment form
    clients = Client.query.filter_by(active=True).all()
    return render_template('inventory/pdv.html', clients=clients)

@inventory_bp.route('/process-sale', methods=['POST'])
@login_required
def process_sale():
    cart_items = request.json.get('cart_items', [])
    payment_method = request.json.get('payment_method')
    client_id = request.json.get('client_id')

    if not cart_items:
        return jsonify({'error': 'Carrinho vazio'}), 400

    try:
        total_amount = 0

        # Process each item in cart
        for item in cart_items:
            if item['type'] == 'inventory':
                # Update inventory
                inv_item = InventoryItem.query.get(item['id'])
                if not inv_item or inv_item.quantity < item['quantity']:
                    return jsonify({'error': f'Estoque insuficiente para {item["name"]}'}), 400

                inv_item.quantity -= item['quantity']
                total_amount += item['price'] * item['quantity']

        # Create financial entry
        financial_entry = FinancialEntry(
            type='income',
            category='sale',
            amount=total_amount,
            description='Venda PDV',
            date=datetime.now(),
            payment_method=payment_method,
            client_id=client_id if client_id else None
        )

        db.session.add(financial_entry)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Venda realizada com sucesso!',
            'sale_id': financial_entry.id
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@inventory_bp.route('/update-quantity/<int:item_id>', methods=['POST'])
@login_required
def update_quantity(item_id):
    inventory_item = InventoryItem.query.get_or_404(item_id)
    new_quantity = request.form.get('quantity', type=int)

    if new_quantity is not None and new_quantity >= 0:
        inventory_item.quantity = new_quantity
        db.session.commit()
        flash('Quantidade atualizada com sucesso!', 'success')
    else:
        flash('Quantidade inválida.', 'danger')

    return redirect(url_for('inventory.index'))

@inventory_bp.route('/stats')
@login_required
def stats():
    # Get inventory statistics for charts
    normal_stock = InventoryItem.query.filter(InventoryItem.quantity > InventoryItem.minimum_stock).count()
    low_stock = InventoryItem.query.filter(InventoryItem.quantity <= InventoryItem.minimum_stock, InventoryItem.quantity > 0).count()
    out_of_stock = InventoryItem.query.filter(InventoryItem.quantity == 0).count()

    return jsonify({
        'normal': normal_stock,
        'low': low_stock,
        'out': out_of_stock
    })

@inventory_bp.route('/top-items')
@login_required
def top_items():
    # Get top 10 items by quantity
    top_items = InventoryItem.query.order_by(InventoryItem.quantity.desc()).limit(10).all()

    item_names = [item.name for item in top_items]
    quantities = [item.quantity for item in top_items]

    return jsonify({
        'items': item_names,
        'quantities': quantities
    })