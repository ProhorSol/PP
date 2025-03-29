from extensions import db
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # администратор, менеджер, преподаватель, студент
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    group = db.Column(db.String(20), nullable=False)
    course = db.Column(db.Integer, nullable=True)
    full_name = db.Column(db.String(100), nullable=False)
    participations = db.relationship('EventParticipation', backref='student', lazy=True, 
                                   cascade='all, delete-orphan')

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_type = db.Column(db.String(50), nullable=False)  # конференция, спортивное, культурное, волонтерское, другое
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    max_participants = db.Column(db.Integer)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_document = db.Column(db.String(200))  # путь к PDF файлу приказа
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='активно')  # активно, завершено, отменено
    participants = db.relationship('EventParticipation', backref='event', lazy=True,
                                 cascade='all, delete-orphan')

class EventParticipation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    status = db.Column(db.String(20), default='зарегистрирован')  # зарегистрирован, участвовал, завершил
    result_place = db.Column(db.String(50))  # место/результат участия
    award_document = db.Column(db.String(200))  # путь к файлу награды
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
