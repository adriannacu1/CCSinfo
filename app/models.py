from app import db

class Room(db.Model):
    __tablename__ = 'rooms'
    room_id = db.Column(db.Integer, primary_key=True)
    room_name = db.Column(db.String(50), unique=True, nullable=False)
    floor = db.Column(db.Integer, default=1)
    capacity = db.Column(db.Integer, default=0)
    schedules = db.relationship('Schedule', backref='room', lazy=True)

class Faculty(db.Model):
    __tablename__ = 'faculty'
    faculty_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50))
    username = db.Column(db.String(50))
    password = db.Column(db.String(255))
    status_state = db.Column(db.String(25), default='AVAILABLE')
    schedules = db.relationship('Schedule', backref='faculty', lazy=True)

class Section(db.Model):
    __tablename__ = 'sections'
    section_id = db.Column(db.Integer, primary_key=True)
    section_name = db.Column(db.String(50), unique=True, nullable=False)
    course = db.Column(db.String(50))
    year_level = db.Column(db.String(20))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    schedules = db.relationship('Schedule', backref='section', lazy=True)

class Schedule(db.Model):
    __tablename__ = 'schedule'
    schedule_id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id'))
    section_id = db.Column(db.Integer, db.ForeignKey('sections.section_id'))
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.faculty_id'))
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.room_id'))
    day = db.Column(db.String(20))  # Changed from day_of_week to day
    time = db.Column(db.String(50))  # Changed from start_time/end_time to time
    subject = db.Column(db.String(100))  # Added subject field

class Course(db.Model):
    __tablename__ = 'courses'
    course_id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    sections = db.relationship('Section', backref='course_info', lazy=True)

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
    email = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='admin')
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime)
    password_reset_token = db.Column(db.String(255))
    password_reset_expires = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class Event(db.Model):
    __tablename__ = 'events'
    event_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    event_date = db.Column(db.Date)
    event_time = db.Column(db.Time)
    end_time = db.Column(db.Time)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='upcoming')
    featured_image = db.Column(db.String(500))
    created_by = db.Column(db.Integer, db.ForeignKey('admin.admin_id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    speakers = db.relationship('EventSpeaker', backref='event', lazy=True, cascade='all, delete-orphan')

class EventSpeaker(db.Model):
    __tablename__ = 'event_speakers'
    speaker_id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.event_id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100))
    bio = db.Column(db.Text)
    avatar = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
