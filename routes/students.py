from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Student, User, db
from werkzeug.security import generate_password_hash
import random
import string

students_bp = Blueprint('students', __name__)

def generate_username(full_name):
    # Транслитерация имени для создания username
    translit = {'а':'a','б':'b','в':'v','г':'g','д':'d','е':'e','ё':'e',
      'ж':'zh','з':'z','и':'i','й':'y','к':'k','л':'l','м':'m','н':'n',
      'о':'o','п':'p','р':'r','с':'s','т':'t','у':'u','ф':'f','х':'h',
      'ц':'ts','ч':'ch','ш':'sh','щ':'sch','ъ':'','ы':'y','ь':'','э':'e',
      'ю':'yu','я':'ya', 'А':'A','Б':'B','В':'V','Г':'G','Д':'D','Е':'E','Ё':'E',
      'Ж':'Zh','З':'Z','И':'I','Й':'Y','К':'K','Л':'L','М':'M','Н':'N',
      'О':'O','П':'P','Р':'R','С':'S','Т':'T','У':'U','Ф':'F','Х':'H',
      'Ц':'Ts','Ч':'Ch','Ш':'Sh','Щ':'Sch','Ъ':'','Ы':'Y','Ь':'','Э':'E',
      'Ю':'Yu','Я':'Ya',' ':'_'}
    
    username = ''.join(translit.get(c, c) for c in full_name.lower())
    username = ''.join(c for c in username if c.isalnum() or c == '_')
    return username

def generate_password():
    # Генерация случайного пароля
    length = 12
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

@students_bp.route('/students')
@login_required
def list_students():
    students = Student.query.all()
    return render_template('students/list.html', students=students)

@students_bp.route('/students/add', methods=['POST'])
@login_required
def add_student():
    if current_user.role not in ['admin', 'manager', 'teacher']:
        flash('Недостаточно прав для добавления студентов')
        return redirect(url_for('students.list_students'))

    full_name = request.form.get('full_name')
    group = request.form.get('group')
    course = request.form.get('course')

    if not full_name or not group or not course:
        flash('Все поля должны быть заполнены')
        return redirect(url_for('students.list_students'))

    try:
        # Создаем пользователя для студента
        username = generate_username(full_name)
        password = generate_password()
        
        # Добавляем случайное число к username, если такой уже существует
        base_username = username
        counter = 1
        while User.query.filter_by(username=username).first() is not None:
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role='student',
            email=f"{username}@example.com"  # Временный email
        )
        db.session.add(user)
        db.session.flush()  # Получаем id пользователя
        
        # Создаем студента
        student = Student(
            user_id=user.id,
            full_name=full_name,
            group=group,
            course=int(course)  # Преобразуем строку в число
        )
        db.session.add(student)
        db.session.commit()
        
        flash(f'Студент успешно добавлен. Логин: {username}, Пароль: {password}')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при добавлении студента: {str(e)}')

    return redirect(url_for('students.list_students'))

@students_bp.route('/students/<int:student_id>/edit', methods=['POST'])
@login_required
def edit_student(student_id):
    if current_user.role not in ['admin', 'manager', 'teacher']:
        flash('Недостаточно прав для редактирования студентов')
        return redirect(url_for('students.list_students'))

    student = Student.query.get_or_404(student_id)
    full_name = request.form.get('full_name')
    group = request.form.get('group')

    if not full_name or not group:
        flash('Все поля должны быть заполнены')
        return redirect(url_for('students.list_students'))

    try:
        student.full_name = full_name
        student.group = group
        db.session.commit()
        flash('Данные студента успешно обновлены')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при обновлении данных студента: {str(e)}')

    return redirect(url_for('students.list_students'))

@students_bp.route('/students/<int:student_id>/delete', methods=['POST'])
@login_required
def delete_student(student_id):
    if current_user.role not in ['admin', 'manager', 'teacher']:
        flash('Недостаточно прав для удаления студентов')
        return redirect(url_for('students.list_students'))

    student = Student.query.get_or_404(student_id)
    try:
        # Если у студента есть связанный пользователь, удаляем его
        if student.user_id:
            user = User.query.get(student.user_id)
            if user:
                db.session.delete(user)
        
        # Удаляем студента (связанные participations удалятся автоматически благодаря cascade)
        db.session.delete(student)
        db.session.commit()
        flash('Студент успешно удален')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении студента: {str(e)}')

    return redirect(url_for('students.list_students'))
