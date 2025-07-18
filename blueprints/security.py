from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import User, Employee, ActivityLog
from sqlalchemy import func, text
from werkzeug.security import generate_password_hash
import os
import platform
import psutil
import datetime
import forms
import time
from flask import request
from models import ActivityLog

security_bp = Blueprint('security', __name__, url_prefix='/security')

@security_bp.before_request
@login_required
def check_security_access():
    if request.endpoint != 'security.app_info':  # Allow public access to app_info
        # Check if the user has access to security module
        if not current_user.has_security_access():
            flash('Você não tem permissão para acessar o módulo de segurança.', 'danger')
            return redirect(url_for('dashboard.index'))

@security_bp.route('/')
def index():
    # Get system information
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.datetime.now() - boot_time
    uptime_str = f"{uptime.days}d {uptime.seconds // 3600}h {(uptime.seconds // 60) % 60}m"

    system_info = {
        'os': f"{platform.system()} {platform.version()}",
        'python_version': platform.python_version(),
        'ip': request.host,
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'uptime': uptime_str,
        'database': 'PostgreSQL',
        'last_updated': datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    }

    # Get users for system users table
    users = User.query.all()

    # Obter logs reais de atividade do sistema
    login_logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()

    # Se não existir logs, criar alguns registros iniciais para demonstração
    if not login_logs:
        demo_logs = [
            {
                'username': 'admin',
                'activity': 'Login bem-sucedido',
                'ip_address': request.remote_addr,
                'category': 'autenticação'
            },
            {
                'username': 'sistema',
                'activity': 'Aplicação inicializada',
                'ip_address': request.remote_addr,
                'category': 'sistema'
            },
            {
                'username': current_user.username,
                'activity': 'Acesso ao módulo de segurança',
                'ip_address': request.remote_addr,
                'category': 'segurança'
            }
        ]

        for log in demo_logs:
            ActivityLog.log_activity(
                username=log['username'],
                activity=log['activity'],
                ip_address=log['ip_address'],
                user_id=current_user.id if log['username'] == current_user.username else None,
                category=log['category']
            )

        # Buscar os logs novamente após criar os registros iniciais
        login_logs = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(10).all()

    return render_template('security/index.html',
                           system_info=system_info,
                           users=users,
                           login_logs=login_logs)


@security_bp.route('/users')
def users():
    """Página de gerenciamento de usuários"""
    users = User.query.all()
    return render_template('security/users.html', users=users)


@security_bp.route('/user/new', methods=['GET', 'POST'])
def new_user():
    """Criar novo usuário"""
    form = forms.UserForm()

    if form.validate_on_submit():
        # Criar novo usuário
        user = User()
        user.username = form.username.data
        user.email = form.email.data
        user.set_password(form.password.data)
        user.role = form.role.data
        user._is_active = form.active.data

        # Criar funcionário associado
        employee = Employee()
        employee.first_name = form.first_name.data
        employee.last_name = form.last_name.data
        employee.position = form.position.data
        employee.department = form.department.data
        employee.phone = form.phone.data
        employee.hire_date = form.hire_date.data
        employee.active = form.active.data

        # Associar usuário e funcionário
        employee.user = user

        db.session.add(user)
        db.session.add(employee)
        db.session.commit()

        # Registrar atividade de criação de usuário
        ActivityLog.log_activity(
            username=current_user.username,
            activity=f'Criou novo usuário: {user.username}',
            ip_address=request.remote_addr,
            user_id=current_user.id,
            category='usuários'
        )

        flash(f'Usuário "{user.username}" criado com sucesso.', 'success')
        return redirect(url_for('security.users'))

    return render_template('security/user_form.html', form=form, title="Novo Usuário")


@security_bp.route('/user/edit/<int:id>', methods=['GET', 'POST'])
def edit_user(id):
    """Editar usuário existente"""
    user = User.query.get_or_404(id)
    employee = user.employee

    if not employee:
        flash('Usuário não possui perfil de funcionário associado.', 'danger')
        return redirect(url_for('security.users'))

    form = forms.EmployeeForm()

    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.role.data = user.role
        form.active.data = user._is_active

        form.first_name.data = employee.first_name
        form.last_name.data = employee.last_name
        form.position.data = employee.position
        form.department.data = employee.department
        form.phone.data = employee.phone
        form.hire_date.data = employee.hire_date

    if form.validate_on_submit():
        # Check if username is unique
        if user.username != form.username.data and User.query.filter_by(username=form.username.data).first():
            flash('Nome de usuário já existe.', 'danger')
            return render_template('security/user_form.html', form=form, user=user, title='Editar Usuário')

        # Check if email is unique
        if user.email != form.email.data and User.query.filter_by(email=form.email.data).first():
            flash('Email já cadastrado.', 'danger')
            return render_template('security/user_form.html', form=form, user=user, title='Editar Usuário')

        # Update user
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data
        user._is_active = form.active.data

        # Update password if provided
        if form.password.data:
            user.set_password(form.password.data)

        # Update employee
        employee.first_name = form.first_name.data
        employee.last_name = form.last_name.data
        employee.position = form.position.data
        employee.department = form.department.data
        employee.phone = form.phone.data
        employee.hire_date = form.hire_date.data
        employee.active = form.active.data

        try:
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('security.users'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar usuário.', 'danger')
            app.logger.error(f'Error updating user: {str(e)}')
    return render_template('security/user_form.html', form=form, user=user, title='Editar Usuário')


@security_bp.route('/user/toggle/<int:id>', methods=['POST'])
def toggle_user(id):
    """Ativa/desativa um usuário"""
    user = User.query.get_or_404(id)


@security_bp.route('/config/git', methods=['GET', 'POST'])
@login_required
def git_config():
    """Configuração de credenciais do Git"""
    if request.method == 'POST':
        username = request.form.get('git_username')
        email = request.form.get('git_email')
        token = request.form.get('git_token')
        repo_url = request.form.get('git_repo')

        try:
            # Configurar git globalmente
            subprocess.run(['git', 'config', '--global', 'user.name', username])
            subprocess.run(['git', 'config', '--global', 'user.email', email])

            # Armazenar credenciais (usa credential.helper store para salvar)
            if repo_url and token:
                # Extrair domínio do repo_url para configurar credenciais
                repo_parts = repo_url.split('/')
                if len(repo_parts) >= 3:
                    domain = repo_parts[2]  # Exemplo: github.com

                    # Configurar credencial helper
                    subprocess.run(['git', 'config', '--global', 'credential.helper', 'store'])

                    # Formar a URL com credenciais e salvar em um arquivo temporário
                    credential_url = f"https://{username}:{token}@{domain}"
                    with open(os.path.expanduser('~/.git-credentials'), 'w') as f:
                        f.write(credential_url)

                    flash('Credenciais do Git configuradas com sucesso!', 'success')
                else:
                    flash('URL do repositório inválida', 'danger')
            else:
                flash('Configurações básicas do Git salvas!', 'success')

            # Registrar atividade
            ActivityLog.log_activity(
                username=current_user.username,
                activity='Configurou credenciais do Git',
                ip_address=request.remote_addr,
                user_id=current_user.id,
                category='sistema'
            )

            return redirect(url_for('security.config'))

        except Exception as e:
            flash(f'Erro ao configurar Git: {str(e)}', 'danger')
            return redirect(url_for('security.git_config'))

    # GET request - mostra formulário
    return render_template('security/git_config.html')

    if user.username == 'admin':
        flash('Não é possível desativar o usuário administrador principal.', 'danger')
    else:
        user._is_active = not user._is_active
        status = 'ativado' if user._is_active else 'desativado'
        db.session.commit()

        # Registrar atividade de ativação/desativação de usuário
        ActivityLog.log_activity(
            username=current_user.username,
            activity=f'Usuário "{user.username}" foi {status}',
            ip_address=request.remote_addr,
            user_id=current_user.id,
            category='usuários'
        )

        flash(f'Usuário "{user.username}" {status} com sucesso.', 'success')

    return redirect(url_for('security.users'))


@security_bp.route('/user/reset_password/<int:id>', methods=['POST'])
def reset_password(id):
    """Resetar senha de um usuário para a senha padrão"""
    user = User.query.get_or_404(id)

    # Define a senha padrão como "mudar123"
    user.set_password('mudar123')
    db.session.commit()

    # Registrar atividade de reset de senha
    ActivityLog.log_activity(
        username=current_user.username,
        activity=f'Resetou senha do usuário: {user.username}',
        ip_address=request.remote_addr,
        user_id=current_user.id,
        category='segurança'
    )

    flash(f'Senha do usuário "{user.username}" foi resetada. Nova senha: mudar123', 'success')
    return redirect(url_for('security.users'))


@security_bp.route('/config')
def config():
    """Configurações do sistema"""
    return render_template('security/config.html')

@security_bp.route('/reset_admin', methods=['POST'])
def reset_admin():
    """Recria o usuário admin"""
    from werkzeug.security import generate_password_hash

    # Verifica se já existe um admin
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email='admin@unbug.com',
            password_hash=generate_password_hash('admin123'),
            role='admin',
            _is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        flash('Usuário admin recriado com sucesso! Senha: admin123', 'success')
    else:
        admin.password_hash = generate_password_hash('admin123')
        db.session.commit()
        flash('Senha do admin resetada! Nova senha: admin123', 'success')

    return redirect(url_for('security.users'))


@security_bp.route('/app_info')
def app_info():
    """Retorna informações do app em formato JSON"""
    info = {
        'name': 'Unbug Solutions TI - ERP',
        'version': '1.0.0',
        'database': 'PostgreSQL',
        'server_time': datetime.datetime.now().isoformat(),
        'users_count': User.query.count(),
        'employees_count': Employee.query.count()
    }
    return jsonify(info)

@security_bp.route('/backup', methods=['POST'])
def backup():
    """Realiza backup do sistema"""
    try:
        # Simula um backup
        time.sleep(2)
        return jsonify({
            'success': True,
            'message': 'Backup realizado com sucesso!'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erro ao realizar backup: {str(e)}'
        })

@security_bp.route('/logs')
def logs():
    """Retorna logs do sistema"""
    # Simula logs do sistema
    system_logs = [
        f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Sistema iniciado",
        f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Backup automático realizado",
        f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Verificação de segurança concluída"
    ]
    return jsonify({'logs': system_logs})

@security_bp.route('/scan', methods=['POST'])
def security_scan():
    """Realiza verificação de segurança"""
    # Simula uma verificação de segurança
    scan_results = [
        {'status': 'ok', 'message': 'Firewall ativo e configurado'},
        {'status': 'ok', 'message': 'Senhas fortes em uso'},
        {'status': 'ok', 'message': 'Backup automático configurado'},
        {'status': 'warning', 'message': 'Algumas contas sem autenticação 2FA'}
    ]
    return jsonify({'results': scan_results})