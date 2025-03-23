from flask import Flask
from extensions import db, login_manager
from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'default-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///database.db')
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

# Инициализация расширений
db.init_app(app)
login_manager.init_app(app)

# Настройка login_manager
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
