# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.sql import func
import pytz

IST = pytz.timezone("Asia/Kolkata")

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    profile_pic_url = db.Column(db.String(20), nullable=False, default='default-profile-pic.png')
    
    # --- UPDATED & NEW PROFILE FIELDS ---
    first_name = db.Column(db.String(80))
    last_name = db.Column(db.String(80))
    bio = db.Column(db.Text)
    role = db.Column(db.String(80))       # e.g., 'Professional', 'Student', 'Hobbyist'
    organization = db.Column(db.String(120)) # Company or University
    website_url = db.Column(db.String(200))

    # Relationships to other tables
    investigations = db.relationship('Investigation', backref='author', lazy=True)
    reports = db.relationship('Report', backref='author', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    def _repr_(self):
        return f'<User {self.username}>'

# --- NEW MODELS ---
# --- UPDATED Investigation MODEL ---
class Investigation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150))
    drone_type = db.Column(db.String(50))
    description = db.Column(db.Text)
    drone_photo = db.Column(db.String(20), nullable=False, default='default-drone.png') # For user-uploaded photos
    status = db.Column(db.String(20), nullable=False, default='Live') # Default status is now 'Live'
    # AFTER (Correct):
    timestamp = db.Column(
        db.DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(IST)
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    captures = db.relationship('Capture', backref='investigation', lazy=True, cascade='all, delete-orphan')

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    file_type = db.Column(db.String(10), nullable=False) # e.g., 'pdf', 'doc', 'csv'
    timestamp = db.Column(
        db.DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(IST)
    )
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class ThreadFeedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50), nullable=False) # Font Awesome icon class
    timestamp = db.Column(
        db.DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(IST)
    )
    
    
# ADD THIS NEW MODEL AT THE END OF THE FILE
class Capture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_filename = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(
        db.DateTime(timezone=True), 
        nullable=False, 
        default=lambda: datetime.now(IST)
    )
    investigation_id = db.Column(db.Integer, db.ForeignKey('investigation.id'), nullable=False)

    def _repr_(self):
        return f"Capture('{self.image_filename}', Investigation ID: {self.investigation_id})"