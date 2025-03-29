from flask import render_template
from config import app, db, login_manager
from models import User
import os

# Настройка папки для загрузки файлов
app.static_folder = 'static'
app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Импорт маршрутов
from routes.auth import auth_bp
from routes.events import events_bp
from routes.students import students_bp

# Регистрация маршрутов
app.register_blueprint(auth_bp)
app.register_blueprint(events_bp)
app.register_blueprint(students_bp)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
