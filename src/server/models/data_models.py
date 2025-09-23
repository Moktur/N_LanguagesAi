# from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.server.extensions import db


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    native_language = db.Column(db.String(5), nullable=False)
    created_at = db.Column(db.Date)



class User_Languages(db.Model):
    __tablename__ = 'user_languages'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    language_code = db.Column(db.String(5), nullable=False)
    created_at = db.Column(db.Date)


class Sentences(db.Model):
    __tablename__ = 'sentences'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    original_text = db.Column(db.String(200), nullable=False)
    language_code = db.Column(db.String(5), nullable=False)
    category = db.Column(db.String(50))
    score = db.Column(db.Float, default=0.0)
    last_review = db.Column(db.DateTime, nullable=True)
    next_review = db.Column(db.DateTime, nullable=True)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.Date)


class Sessions(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentences.id'), nullable=False)
    input = db.Column(db.JSON, nullable=True)
    score = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



