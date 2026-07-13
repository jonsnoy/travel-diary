from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), default='default_avatar.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    travels = db.relationship('Travel', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Travel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    
    # Местоположение
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    location_address = db.Column(db.String(300))
    
    # Стоимость
    cost_amount = db.Column(db.Float, default=0)
    cost_currency = db.Column(db.String(3), default='RUB')
    cost_details = db.Column(db.Text)
    
    # Даты
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    
    # Оценки
    transport_rating = db.Column(db.Integer, default=3)
    safety_rating = db.Column(db.Integer, default=3)
    population_rating = db.Column(db.Integer, default=3)
    vegetation_rating = db.Column(db.Integer, default=3)
    
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения
    images = db.relationship('TravelImage', backref='travel', lazy=True, cascade='all, delete-orphan')
    cultural_sites = db.relationship('CulturalSite', backref='travel', lazy=True, cascade='all, delete-orphan')
    places_to_visit = db.relationship('PlaceToVisit', backref='travel', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Travel {self.title}>'

class TravelImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_id = db.Column(db.Integer, db.ForeignKey('travel.id'), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(300))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class CulturalSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_id = db.Column(db.Integer, db.ForeignKey('travel.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    visited = db.Column(db.Boolean, default=False)

class PlaceToVisit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    travel_id = db.Column(db.Integer, db.ForeignKey('travel.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(10), default='medium')  # low, medium, high