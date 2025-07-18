from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, DateField, DecimalField, IntegerField, BooleanField, FileField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, NumberRange, ValidationError
from flask_wtf.file import FileAllowed
from datetime import date

from models import User

# Authentication Forms
class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nova Senha', validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Alterar Senha')

class UserForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[Optional(), Length(min=6)])
    role = SelectField('Nível de Acesso', choices=[
        ('admin', 'Administrador'),
        ('management', 'Gerência'),
        ('employee', 'Funcionário')
    ])
    active = BooleanField('Ativo')
    submit = SubmitField('Salvar')

class EmployeeForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[Optional(), Length(min=6)])
    role = SelectField('Nível de Acesso', choices=[
        ('admin', 'Administrador'),
        ('management', 'Gerência'),
        ('employee', 'Funcionário')
    ])
    first_name = StringField('Nome', validators=[DataRequired()])
    last_name = StringField('Sobrenome', validators=[DataRequired()])
    position = StringField('Cargo', validators=[DataRequired()])
    department = StringField('Departamento', validators=[DataRequired()])
    phone = StringField('Telefone', validators=[DataRequired()])
    hire_date = DateField('Data de Contratação', validators=[DataRequired()])
    active = BooleanField('Ativo')
    submit = SubmitField('Salvar')

class EditEmployeeForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    role = SelectField('Nível de Acesso', choices=[
        ('admin', 'Administrador'),
        ('management', 'Gerência'),
        ('employee', 'Funcionário')
    ])
    first_name = StringField('Nome', validators=[DataRequired()])
    last_name = StringField('Sobrenome', validators=[DataRequired()])
    position = StringField('Cargo', validators=[DataRequired()])
    department = StringField('Departamento', validators=[DataRequired()])
    phone = StringField('Telefone', validators=[DataRequired()])
    hire_date = DateField('Data de Contratação', validators=[DataRequired()])
    active = BooleanField('Ativo')
    submit = SubmitField('Salvar')

class ClientForm(FlaskForm):
    name = StringField('Nome/Empresa', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Telefone', validators=[DataRequired()])
    address = StringField('Endereço', validators=[DataRequired()])
    city = StringField('Cidade', validators=[DataRequired()])
    state = StringField('Estado', validators=[DataRequired()])
    zip_code = StringField('CEP', validators=[DataRequired()])
    contact_person = StringField('Pessoa de Contato')
    active = BooleanField('Ativo')
    submit = SubmitField('Salvar')

class SupplierForm(FlaskForm):
    name = StringField('Nome/Empresa', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Telefone', validators=[DataRequired()])
    address = StringField('Endereço', validators=[DataRequired()])
    city = StringField('Cidade', validators=[DataRequired()])
    state = StringField('Estado', validators=[DataRequired()])
    zip_code = StringField('CEP', validators=[DataRequired()])
    contact_person = StringField('Pessoa de Contato')
    active = BooleanField('Ativo')
    submit = SubmitField('Salvar')

class ServiceOrderForm(FlaskForm):
    title = StringField('Título', validators=[DataRequired()])
    description = TextAreaField('Descrição', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('open', 'Aberta'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluída'),
        ('cancelled', 'Cancelada')
    ])
    priority = SelectField('Prioridade', choices=[
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta')
    ])
    client_id = SelectField('Cliente', coerce=int)
    employee_id = SelectField('Responsável', coerce=int)
    start_date = DateField('Data de Início', validators=[DataRequired()])
    completion_date = DateField('Data de Conclusão', validators=[Optional()])
    notes = TextAreaField('Observações')
    submit = SubmitField('Salvar')

class ProjectForm(FlaskForm):
    name = StringField('Nome do Projeto', validators=[DataRequired()])
    description = TextAreaField('Descrição', validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('planning', 'Planejamento'),
        ('in_progress', 'Em Andamento'),
        ('on_hold', 'Em Espera'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado')
    ])
    client_id = SelectField('Cliente', coerce=int)
    manager_id = SelectField('Gerente do Projeto', coerce=int)
    start_date = DateField('Data de Início', validators=[DataRequired()])
    end_date = DateField('Data de Conclusão Prevista', validators=[Optional()])
    budget = DecimalField('Orçamento', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Salvar')

class StockItemForm(FlaskForm):
    name = StringField('Nome do Item', validators=[DataRequired()])
    description = TextAreaField('Descrição')
    sku = StringField('SKU/Código', validators=[DataRequired()])
    category = StringField('Categoria', validators=[DataRequired()])
    quantity = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=0)])
    minimum_stock = IntegerField('Estoque Mínimo', validators=[DataRequired(), NumberRange(min=0)])
    unit_price = DecimalField('Preço Unitário', validators=[DataRequired(), NumberRange(min=0)])
    location = StringField('Localização')
    supplier_id = SelectField('Fornecedor', coerce=int)
    submit = SubmitField('Salvar')

class StoreItemForm(FlaskForm):
    name = StringField('Nome do Item', validators=[DataRequired()])
    description = TextAreaField('Descrição')
    sku = StringField('SKU/Código', validators=[DataRequired()])
    category = StringField('Categoria', validators=[DataRequired()])
    quantity = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=0)])
    minimum_stock = IntegerField('Estoque Mínimo', validators=[DataRequired(), NumberRange(min=0)])
    unit_price = DecimalField('Preço Unitário', validators=[DataRequired(), NumberRange(min=0)])
    location = StringField('Localização')
    supplier_id = SelectField('Fornecedor', coerce=int)
    submit = SubmitField('Salvar')

class FinancialEntryForm(FlaskForm):
    type = SelectField('Tipo', choices=[
        ('income', 'Receita'),
        ('expense', 'Despesa')
    ])
    category = StringField('Categoria', validators=[DataRequired()])
    amount = DecimalField('Valor', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Descrição', validators=[DataRequired()])
    date = DateField('Data', validators=[DataRequired()])
    invoice_number = StringField('Número da Fatura/Nota Fiscal')
    payment_method = SelectField('Método de Pagamento', choices=[
        ('money', 'Dinheiro'),
        ('credit_card', 'Cartão de Crédito'),
        ('debit_card', 'Cartão de Débito'),
        ('bank_transfer', 'Transferência Bancária'),
        ('check', 'Cheque'),
        ('other', 'Outro')
    ])
    client_id = SelectField('Cliente', coerce=int)
    supplier_id = SelectField('Fornecedor', coerce=int)
    service_order_id = SelectField('Ordem de Serviço', coerce=int)
    project_id = SelectField('Projeto', coerce=int)
    invoice_file = FileField('Anexar Documento', validators=[
        Optional(),
        FileAllowed(['pdf', 'jpg', 'png'], 'Somente arquivos PDF, JPG ou PNG são permitidos.')
    ])
    submit = SubmitField('Salvar')

class OrderItemForm(FlaskForm):
    inventory_item_id = SelectField('Item do Estoque', coerce=int)
    quantity = IntegerField('Quantidade', validators=[DataRequired(), NumberRange(min=1)])
    service_order_id = HiddenField()
    submit = SubmitField('Adicionar Item')

class SearchForm(FlaskForm):
    query = StringField('Buscar')
    status = SelectField('Status', choices=[
        ('', 'Todos'),
        ('open', 'Aberta'),
        ('in_progress', 'Em Andamento'),
        ('completed', 'Concluída'),
        ('cancelled', 'Cancelada')
    ])
    date_from = DateField('De', validators=[Optional()])
    date_to = DateField('Até', validators=[Optional()])
    submit = SubmitField('Buscar')