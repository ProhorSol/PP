from config import app
from models import db, User
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        # Удаляем все таблицы
        db.drop_all()
        
        # Создаем все таблицы заново
        db.create_all()
        
        # Создаем администратора
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            email='admin@example.com',
            role='admin'
        )
        
        # Добавляем администратора в базу данных
        db.session.add(admin)
        db.session.commit()
        
        print('База данных успешно инициализирована!')
        print('Создан администратор:')
        print('Логин: admin')
        print('Пароль: admin123')

if __name__ == '__main__':
    init_database()
