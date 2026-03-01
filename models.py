from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    password = db.Column(db.String(100))
    role = db.Column(db.String(20))
    rooms = db.relationship('Room', backref='owner', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    location = db.Column(db.String(200))
    price = db.Column(db.Float)
    price_type = db.Column(db.String(20), default='per_day')  # per_day / per_month
    image = db.Column(db.String(200), default='default.jpg')
    is_booked = db.Column(db.Boolean, default=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20), default='Booked')