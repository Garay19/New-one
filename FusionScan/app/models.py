from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_admin = db.Column(db.Boolean, default=False)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    student_lrn = db.Column(db.String(12), unique=True)
    strand = db.Column(db.String(64))
    face_encodings = db.Column(db.LargeBinary)
    attendances = db.relationship('Attendance', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    status = db.Column(db.String(20))  # "Present", "Absent", "Unknown", "Anomaly"
    temperature = db.Column(db.Float)

    def __repr__(self):
        return f'<Attendance {self.user_id} - {self.timestamp} - {self.status}>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))