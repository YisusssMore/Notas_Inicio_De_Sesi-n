# Importar las librerías necesarias de Flask
from flask import Flask, render_template, request, redirect, session, flash
# Importar la extensión para bases de datos SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
# Importar funciones para seguridad de contraseñas
from werkzeug.security import generate_password_hash, check_password_hash
# CLI y utilidades
from flask.cli import with_appcontext
import click

# Crear la aplicación Flask
app = Flask(__name__)
# Clave secreta para sesiones y seguridad de la app
app.secret_key = 'super-secret-key'  # Cambia esto por una clave segura en producción
# Configurar la base de datos SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///diary.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Inicializar la base de datos con la app
# Esto permite usar db.Model para crear tablas
# y db.session para interactuar con la base de datos
# (agregar, consultar, modificar, eliminar datos)
db = SQLAlchemy(app)

# Definir la tabla Card para las entradas del diario
class Card(db.Model):
    # id: identificador único de cada tarjeta
    id = db.Column(db.Integer, primary_key=True)
    # title: título de la tarjeta
    title = db.Column(db.String(100), nullable=False)
    # subtitle: descripción corta
    subtitle = db.Column(db.String(300), nullable=False)
    # text: contenido principal de la tarjeta
    text = db.Column(db.Text, nullable=False)

    # Representación de la tarjeta (útil para depuración)
    def __repr__(self):
        return f'<Card {self.id}>'
    
# Asignación #2. Crear la tabla Usuario
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    login = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(120), nullable=False) 
    def __repr__(self):
        return f'<User {self.login}>'
    

# TODO: Implementa el modelo `User` heredando de `db.Model`.
# Debe incluir las columnas:
# - id: db.Integer, primary_key=True, autoincrement=True
# - login: db.String(100), nullable=False
# - password: db.String(128), nullable=False (almacenará el hash de la contraseña)
# Pistas:
# - Usa `generate_password_hash(password)` para guardar contraseñas de forma segura.
# - Define una clave primaria (sin esto SQLAlchemy no podrá mapear el modelo).
# - Cuando esté listo, podrás usar `User.query` en las rutas de login/registro.

# Ruta principal: login de usuario
@app.route('/', methods=['GET','POST'])
def login():
        error = ''
        if request.method == 'POST':
            # Obtener datos del formulario
            form_login = request.form['email']
            form_password = request.form['password']
            #Asignación #4. Aplicar la autorización
            # Buscar usuario por login y verificar contraseña usando hash seguro
            user = User.query.filter_by(login=form_login).first()
            if user and check_password_hash(user.password, form_password):
                # Guardar datos del usuario en la sesión para mantenerlo logueado
                session['user_id'] = user.id
                session['user_login'] = user.login
                return redirect('/index')
            else:
                error = 'Nombre de usuario o contraseña incorrectos'
                # Mostrar mensaje de error usando flash
                flash(error, 'danger')
            return render_template('login.html', error=error)
        else:
            # Si es GET, mostrar el formulario de login
            return render_template('login.html')

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    # Limpiar la sesión y mostrar mensaje
    session.clear()
    flash('Sesión cerrada correctamente.', 'info')
    return redirect('/')

# Ruta de registro de usuario
@app.route('/reg', methods=['GET','POST'])
def reg():
    if request.method == 'POST':
        # Obtener datos del formulario
        login= request.form['email']
        password = request.form['password']
        # Asignación #3. Hacer que los datos del usuario se registren en la base de datos.
        # TODO: Implementa el flujo de registro:
        # 1) Verifica si ya existe un usuario con ese correo:
        #    existing_user = User.query.filter_by(login=login).first()
        ususario_existente = User.query.filter_by(login=login).first()
        # 2) Si existe, muestra un mensaje (flash) y vuelve al formulario.
        if ususario_existente :
            flash('Ese usuario ya existe. Intenta con otro correo.', 'warning')
            return render_template('registration.html')
        
        # 3) Si no existe, crea el objeto User, asigna login y
        #    guarda el hash de la contraseña: generate_password_hash(password).
        hash_password = generate_password_hash(password)
        nuevo_usuario= User(login=login, password=hash_password)

        # 4) Guarda en la base de datos con db.session.add(...) y db.session.commit().
        db.session.add(nuevo_usuario)
        db.session.commit()
        # 5) Muestra un mensaje de éxito y redirige al login.
        flash('Usuario registrado correctamente. ¡Ahora puedes iniciar sesión!', 'info')
        return render_template('registration.html')
    else:
        # Si es GET, mostrar el formulario de registro
        return render_template('registration.html')

# Decorador para requerir login en rutas protegidas
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Si el usuario no está logueado, redirigir al login
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

# Página principal después de iniciar sesión
@app.route('/index')
@login_required
def index():
    # Visualización de las entradas de la base de datos
    # Consulta todas las tarjetas ordenadas por id
    cards = Card.query.order_by(Card.id).all()
    return render_template('index.html', cards=cards)

# Página para ver una tarjeta específica
@app.route('/card/<int:id>')
@login_required
def card(id):
    # Buscar la tarjeta por id
    card = Card.query.get(id)
    return render_template('card.html', card=card)

# Página para mostrar el formulario de creación de tarjeta
@app.route('/create')
@login_required
def create():
    return render_template('create_card.html')

# El formulario de inscripción de nuevas tarjetas
@app.route('/form_create', methods=['GET','POST'])
@login_required
def form_create():
    if request.method == 'POST':
        # Obtener datos del formulario
        title =  request.form['title']
        subtitle = request.form['subtitle']
        text = request.form['text']

        # Creación de un objeto que se enviará a la base de datos
        card = Card()
        card.title = title
        card.subtitle = subtitle
        card.text = text

        db.session.add(card)
        db.session.commit()
        flash('Tarjeta creada correctamente.', 'success')
        # Redirigir a la página principal después de crear la tarjeta
        return redirect('/index')
    else:
        # Si es GET, mostrar el formulario de creación
        return render_template('create_card.html')

# Función CLI para inicializar la base de datos (con contexto de app)
@app.cli.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()
    click.echo("Base de datos inicializada.")
    #
    # Pasos robustos para inicializar la BD en distintos terminales:
    #
    # Opción recomendada (no requiere variables de entorno):
    #   flask --app main init-db
    #   flask --app main run
    #
    # Si prefieres usar FLASK_APP:
    #   Git Bash:
    #     export FLASK_APP=main
    #     flask init-db && flask run
    #   PowerShell:
    #     $env:FLASK_APP = "main"
    #     flask init-db; flask run
    #   CMD (Símbolo del sistema):
    #     set FLASK_APP=main
    #     flask init-db && flask run
    #
    # Opción totalmente independiente del shell (sin activar venv):
    #   .\venv\Scripts\python.exe -m flask --app main init-db
    #   .\venv\Scripts\python.exe -m flask --app main run

# Ejecutar la aplicación en modo debug
if __name__ == "__main__":
    app.run(debug=True)
