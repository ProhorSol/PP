from config import app
from models import User, db
from werkzeug.security import generate_password_hash

def create_superuser():
    with app.app_context():
        # Проверяем, существует ли уже админ
        admin = User.query.filter_by(username='admin').first()
        if admin:
            print('Администратор уже существует!')
            return

        # Создаем администратора
        superuser = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            email='admin@example.com',
            role='admin'
        )
        
        # Добавляем в базу данных
        db.session.add(superuser)
        db.session.commit()
        print('Администратор успешно создан!')
        print('Логин: admin')
        print('Пароль: admin123')

if __name__ == '__main__':
    create_superuser()
