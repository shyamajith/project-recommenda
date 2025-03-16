from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    language = db.Column(db.String(50), nullable=False)
    favorite_author = db.Column(db.String(100), nullable=False)
    genres = db.Column(db.String(255), nullable=False)  # Store genres as a comma-separated string
