from flask import Blueprint, render_template, redirect, url_for, flash, request
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
    return render_template('events/list.html', events=events)

@events_bp.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if current_user.role not in ['admin', 'manager']:
        flash('Недостаточно прав')
        return redirect(url_for('events.events_list'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        event_type = request.form.get('event_type')
        date_str = request.form.get('date')
        location = request.form.get('location')
        max_participants = request.form.get('max_participants')
        
        # Конвертируем строку даты в объект datetime
        try:
            date = datetime.fromisoformat(date_str)
        except ValueError:
            flash('Неверный формат даты')
            return redirect(url_for('events.create_event'))
        
        order_file = request.files.get('order_document')
        order_document = None
        if order_file and allowed_file(order_file.filename):
            filename = secure_filename(order_file.filename)
            # Создаем папку uploads, если она не существует
            os.makedirs(os.path.join(app.static_folder, 'uploads'), exist_ok=True)
            # Сохраняем файл в static/uploads
            order_file.save(os.path.join(app.static_folder, 'uploads', filename))
            order_document = filename
            
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
            flash('Ошибка при создании мероприятия')
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
        
    participation_id = request.form.get('participation_id')
    result_place = request.form.get('result_place')
    comment = request.form.get('comment')
    
    participation = EventParticipation.query.get_or_404(participation_id)
    
    award_file = request.files.get('award_document')
    if award_file and allowed_file(award_file.filename):
        filename = secure_filename(award_file.filename)
        award_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        participation.award_document = filename
        
    participation.result_place = result_place
    participation.comment = comment
    participation.status = 'completed'
    
    db.session.commit()
    return redirect(url_for('events.events_list'))
