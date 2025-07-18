from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from app import db
from models import User, ActivityLog
from forms import LoginForm, ChangePasswordForm
from datetime import datetime

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        user = User.query.filter_by(username=username).first()

        if user and password is not None and check_password_hash(user.password_hash, password):
            login_user(user)
            # Use employee first_name if available, otherwise use username
            display_name = user.employee.first_name if user.employee else user.username
            flash(f'Bem vindo, {display_name}!', 'success')

            # Check if there's a 'next' parameter in the request, redirecting to that page if it exists
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)

            # Update user's last login info
            user.last_login = datetime.now()
            user.login_count += 1
            db.session.commit()

            # Registrar atividade de login bem-sucedido
            ActivityLog.log_activity(
                username=user.username,
                activity='Login bem-sucedido',
                ip_address=request.remote_addr,
                user_id=user.id,
                category='autenticação'
            )

            return redirect(url_for('dashboard.index'))

        flash('Usuário ou senha inválidos.', 'danger')

    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    username = current_user.username
    user_id = current_user.id

    # Registrar atividade de logout
    ActivityLog.log_activity(
        username=username,
        activity='Logout realizado',
        ip_address=request.remote_addr,
        user_id=user_id,
        category='autenticação'
    )

    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()

    if form.validate_on_submit():
        current_password = form.current_password.data
        if current_password is not None and check_password_hash(current_user.password_hash, current_password):
            # Set the new password
            new_password = form.new_password.data
            if new_password is not None:
                current_user.password_hash = generate_password_hash(new_password)
            db.session.commit()

            flash('Senha alterada com sucesso!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Senha atual incorreta.', 'danger')

    return render_template('auth/change_password.html', form=form)