from app import db

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(50))
    year_level = db.Column(db.Integer)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'))

class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50))
    schedules = db.relationship('Schedule', backref='faculty', lazy=True)

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(20), unique=True, nullable=False)
    schedules = db.relationship('Schedule', backref='room', lazy=True)

class Section(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(20), unique=True, nullable=False)
    course = db.Column(db.String(50))
    year_level = db.Column(db.String(20))
    students = db.relationship('Student', backref='section', lazy=True)
    schedules = db.relationship('Schedule', backref='section', lazy=True)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String(50))
    day = db.Column(db.String(20))
    subject = db.Column(db.String(50))
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'))
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'))
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
