from app import db

class Room(db.Model):
    __tablename__ = 'rooms'
    # Should be room_id not id to match foreign key references
    room_id = db.Column(db.Integer, primary_key=True)  # Change from 'id' to 'room_id'
    room_name = db.Column(db.String(50), unique=True, nullable=False)
    floor = db.Column(db.Integer, default=1)
    capacity = db.Column(db.Integer, default=0)
    schedules = db.relationship('Schedule', backref='room', lazy=True)

class Faculty(db.Model):
    __tablename__ = 'faculty'
    faculty_id = db.Column(db.Integer, primary_key=True)  # Change from 'id' to 'faculty_id'
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50))
    schedules = db.relationship('Schedule', backref='faculty', lazy=True)

class Section(db.Model):
    __tablename__ = 'sections'
    section_id = db.Column(db.Integer, primary_key=True)  # Change from 'id' to 'section_id'
    section_name = db.Column(db.String(50), unique=True, nullable=False)
    course = db.Column(db.String(50))
    year_level = db.Column(db.String(20))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    students = db.relationship('Student', backref='section', lazy=True)
    schedules = db.relationship('Schedule', backref='section', lazy=True)

class Schedule(db.Model):
    __tablename__ = 'schedule'
    schedule_id = db.Column(db.Integer, primary_key=True)  # Change from 'id' to 'schedule_id'
    time = db.Column(db.String(50))
    day = db.Column(db.String(20))
    subject = db.Column(db.String(50))
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id'))
    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id'))
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.faculty_id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.room_id'))

class Student(db.Model):
    __tablename__ = 'students'
    student_id = db.Column(db.Integer, primary_key=True)  # Change from 'id' to 'student_id'
    student_number = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    course = db.Column(db.String(50))
    year_level = db.Column(db.Integer)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id'))
    email = db.Column(db.String(255), default='')
    status = db.Column(db.String(20), default='Active')
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))

class Course(db.Model):
    __tablename__ = 'courses'
    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    sections = db.relationship('Section', backref='course_info', lazy=True)
    students = db.relationship('Student', backref='course_info', lazy=True)

class Subject(db.Model):
    __tablename__ = 'subjects'
    subject_id = db.Column(db.Integer, primary_key=True)
    subject_name = db.Column(db.String(100), nullable=False)
    schedules = db.relationship('Schedule', backref='subject_info', lazy=True)

class Admin(db.Model):
    __tablename__ = 'admin'
    admin_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
