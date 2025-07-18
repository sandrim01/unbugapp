from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import StockItem, Supplier, ServiceOrder, OrderItem, ActivityLog
from forms import StockItemForm, SearchForm
from sqlalchemy import desc, func
from datetime import datetime
from utils import git_push_changes

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')

@stock_bp.route('/')
@login_required
def index():
    search_form = SearchForm()
    query = StockItem.query

    if request.args.get('query'):
        search_term = f"%{request.args.get('query')}%"
        query = query.filter(StockItem.name.like(search_term) | 
                           StockItem.sku.like(search_term) |
                           StockItem.category.like(search_term))

    items = query.order_by(StockItem.name).all()
    low_stock_items = [item for item in items if item.is_low_stock()]

    return render_template('stock/index.html', 
                         items=items, 
                         low_stock_items=low_stock_items,
                         search_form=search_form)

@stock_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_item():
    form = StockItemForm()
    form.supplier_id.choices = [(0, 'Nenhum')] + [(s.id, s.name) for s in Supplier.query.filter_by(active=True).all()]

    if form.validate_on_submit():
        if StockItem.query.filter_by(sku=form.sku.data).first():
            flash('Já existe um item com este SKU.', 'danger')
            return render_template('stock/create.html', form=form)

        item = StockItem(
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

        # Registrar atividade
        ActivityLog.log_activity(
            username=current_user.username,
            activity=f'Adicionou item ao estoque: {item.name}',
            ip_address=request.remote_addr,
            user_id=current_user.id,
            category='estoque'
        )

        # Enviar alterações para o git
        git_message = f"Adicionado item ao estoque: {item.name} por {current_user.username}"
        git_result = git_push_changes(git_message)

        if git_result:
            flash(f'Item "{item.name}" adicionado com sucesso ao estoque e enviado para o Git.', 'success')
        else:
            flash(f'Item "{item.name}" adicionado com sucesso ao estoque, mas houve um erro ao enviar para o Git.', 'warning')

        return redirect(url_for('stock.index'))

    return render_template('stock/create.html', form=form)

@stock_bp.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = StockItem.query.get_or_404(item_id)
    form = StockItemForm(obj=item)
    form.supplier_id.choices = [(0, 'Nenhum')] + [(s.id, s.name) for s in Supplier.query.filter_by(active=True).all()]

    if form.validate_on_submit():
        if StockItem.query.filter(StockItem.sku == form.sku.data, StockItem.id != item_id).first():
            flash('Já existe um item com este SKU.', 'danger')
            return render_template('stock/edit.html', form=form, item=item)

        item.name = form.name.data
        item.description = form.description.data
        item.sku = form.sku.data
        item.category = form.category.data
        item.quantity = form.quantity.data
        item.minimum_stock = form.minimum_stock.data
        item.unit_price = form.unit_price.data
        item.location = form.location.data
        item.supplier_id = form.supplier_id.data if form.supplier_id.data != 0 else None

        db.session.commit()

        # Registrar atividade
        ActivityLog.log_activity(
            username=current_user.username,
            activity=f'Atualizou item do estoque: {item.name}',
            ip_address=request.remote_addr,
            user_id=current_user.id,
            category='estoque'
        )

        # Enviar alterações para o git
        git_message = f"Atualizado item do estoque: {item.name} por {current_user.username}"
        git_result = git_push_changes(git_message)

        if git_result:
            flash(f'Item "{item.name}" atualizado com sucesso e enviado para o Git.', 'success')
        else:
            flash(f'Item "{item.name}" atualizado com sucesso, mas houve um erro ao enviar para o Git.', 'warning')

        return redirect(url_for('stock.index'))

    return render_template('stock/edit.html', form=form, item=item)

@stock_bp.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    if not current_user.can_delete():
        flash('Você não tem permissão para excluir itens.', 'danger')
        return redirect(url_for('stock.index'))

    item = StockItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()

    flash('Item excluído com sucesso!', 'success')
    return redirect(url_for('stock.index'))

@stock_bp.route('/update-quantity/<int:item_id>', methods=['POST'])
@login_required
def update_quantity(item_id):
    item = StockItem.query.get_or_404(item_id)
    new_quantity = request.form.get('quantity', type=int)

    if new_quantity is not None and new_quantity >= 0:
        item.quantity = new_quantity
        db.session.commit()
        flash('Quantidade atualizada com sucesso!', 'success')
    else:
        flash('Quantidade inválida.', 'danger')

    return redirect(url_for('stock.index'))

@stock_bp.route('/stats')
@login_required
def stats():
    # Get inventory statistics for charts
    normal_stock = StockItem.query.filter(StockItem.quantity > StockItem.minimum_stock).count()
    low_stock = StockItem.query.filter(StockItem.quantity <= StockItem.minimum_stock, StockItem.quantity > 0).count()
    out_of_stock = StockItem.query.filter(StockItem.quantity == 0).count()

    return jsonify({
        'normal': normal_stock,
        'low': low_stock,
        'out': out_of_stock
    })

@stock_bp.route('/top-items')
@login_required
def top_items():
    # Get top 5 items by quantity
    top_items = StockItem.query.order_by(StockItem.quantity.desc()).limit(5).all()

    item_names = [item.name for item in top_items]
    quantities = [item.quantity for item in top_items]

    return jsonify({
        'items': item_names,
        'quantities': quantities
    })
# Comentário para substituir o delimitador que estava causando erro