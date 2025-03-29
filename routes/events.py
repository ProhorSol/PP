from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import Event, EventParticipation, Student, db
import os
from config import app
from datetime import datetime

events_bp = Blueprint('events', __name__)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'jpg', 'jpeg', 'png'}

@events_bp.route('/events')
@login_required
def events_list():
    events = Event.query.all()
    # Получаем список всех студентов для формы внесения результатов
    students = Student.query.all()
    # Для каждого мероприятия подгружаем связанные данные
    for event in events:
        db.session.refresh(event)
    return render_template('events/list.html', events=events, students=students)

@events_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    try:
        if not filename or '..' in filename:
            flash('Некорректное имя файла')
            return redirect(url_for('events.events_list'))
            
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(file_path):
            flash('Файл не найден')
            return redirect(url_for('events.events_list'))
            
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        flash(f'Ошибка при загрузке файла: {str(e)}')
        return redirect(url_for('events.events_list'))

@events_bp.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if current_user.role not in ['admin', 'manager', 'teacher']:
        flash('Недостаточно прав')
        return redirect(url_for('events.events_list'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_type = request.form.get('event_type')
        date_str = request.form.get('date')
        location = request.form.get('location')
        max_participants = request.form.get('max_participants')
        
        try:
            date = datetime.fromisoformat(date_str)
        except ValueError:
            flash('Неверный формат даты')
            return redirect(url_for('events.create_event'))
        
        order_file = request.files.get('order_document')
        order_document = None
        
        if order_file and order_file.filename != '' and allowed_file(order_file.filename):
            try:
                filename = secure_filename(order_file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                order_file.save(file_path)
                order_document = filename
            except Exception as e:
                flash(f'Ошибка при сохранении файла: {str(e)}')
                return redirect(url_for('events.create_event'))
            
        event = Event(
            title=title,
            description=description,
            event_type=event_type,
            date=date,
            location=location,
            max_participants=max_participants if max_participants else None,
            created_by=current_user.id,
            order_document=order_document
        )
        
        try:
            db.session.add(event)
            db.session.commit()
            flash('Мероприятие успешно создано')
            return redirect(url_for('events.events_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при создании мероприятия: {str(e)}')
            return redirect(url_for('events.create_event'))
            
    return render_template('events/create.html')

@events_bp.route('/events/<int:event_id>/participate', methods=['POST'])
@login_required
def participate_event(event_id):
    event = Event.query.get_or_404(event_id)
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if not student:
        flash('Только студенты могут участвовать в мероприятиях')
        return redirect(url_for('events.events_list'))
        
    participation = EventParticipation(
        event_id=event.id,
        student_id=student.id
    )
    db.session.add(participation)
    db.session.commit()
    
    return redirect(url_for('events.events_list'))

@events_bp.route('/events/<int:event_id>/update_result', methods=['POST'])
@login_required
def update_result(event_id):
    if current_user.role not in ['admin', 'manager', 'teacher']:
        flash('Недостаточно прав')
        return redirect(url_for('events.events_list'))
    
    event = Event.query.get_or_404(event_id)
    student_id = request.form.get('student_id')
    result_place = request.form.get('result_place')
    comment = request.form.get('comment')
    
    if not student_id:
        flash('Необходимо выбрать студента')
        return redirect(url_for('events.events_list'))
    
    # Находим или создаем запись об участии
    participation = EventParticipation.query.filter_by(
        event_id=event_id,
        student_id=student_id
    ).first()
    
    if not participation:
        participation = EventParticipation(
            event_id=event_id,
            student_id=student_id
        )
        db.session.add(participation)
    
    participation.result_place = result_place
    participation.comment = comment
    participation.status = 'завершил'
    
    # Обработка загруженного файла
    award_file = request.files.get('award_document')
    if award_file and award_file.filename != '' and allowed_file(award_file.filename):
        try:
            filename = secure_filename(award_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            award_file.save(file_path)
            participation.award_document = filename
        except Exception as e:
            flash(f'Ошибка при сохранении файла: {str(e)}')
            return redirect(url_for('events.events_list'))
    
    try:
        db.session.commit()
        flash('Результаты успешно сохранены')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при сохранении результатов: {str(e)}')
    
    return redirect(url_for('events.events_list'))

@events_bp.route('/events/<int:event_id>/results')
@login_required
def view_results(event_id):
    event = Event.query.get_or_404(event_id)
    participations = EventParticipation.query.filter_by(event_id=event_id).all()
    
    results = []
    for participation in participations:
        if participation.result_place:  # Показываем только тех, у кого есть результаты
            student = Student.query.get(participation.student_id)
            if student:  # Проверяем, что студент существует
                results.append({
                    'student_name': student.full_name if hasattr(student, 'full_name') else 'Неизвестный студент',
                    'place': participation.result_place,
                    'comment': participation.comment,
                    'award_document': participation.award_document
                })
            else:
                results.append({
                    'student_name': 'Неизвестный студент',
                    'place': participation.result_place,
                    'comment': participation.comment,
                    'award_document': participation.award_document
                })
    
    return render_template('events/view_results.html', event=event, results=results)

@events_bp.route('/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event(event_id):
    if current_user.role not in ['admin', 'manager', 'teacher']:
        flash('Недостаточно прав для удаления мероприятий')
        return redirect(url_for('events.events_list'))

    event = Event.query.get_or_404(event_id)
    try:
        # Удаляем файл приказа, если он есть
        if event.order_document:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], event.order_document)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                flash(f'Ошибка при удалении файла приказа: {str(e)}')

        # Удаляем все наградные документы участников
        for participation in event.participants:
            if participation.award_document:
                try:
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], participation.award_document)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except Exception as e:
                    flash(f'Ошибка при удалении наградного документа: {str(e)}')

        # Удаляем мероприятие (связанные записи об участии удалятся автоматически)
        db.session.delete(event)
        db.session.commit()
        flash('Мероприятие успешно удалено')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при удалении мероприятия: {str(e)}')

    return redirect(url_for('events.events_list'))
