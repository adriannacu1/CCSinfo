import os
import sqlite3
import pymysql
from app import app, db
from app.models import Student, Faculty, Room, Section, Schedule

def migrate_from_sqlite_to_mysql():
    # Create all tables in MySQL
    with app.app_context():
        db.create_all()
    
    # Connect to SQLite database
    sqlite_db_path = os.path.join(os.path.dirname(__file__), 'ccs_info.db')
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    
    # Extract data from SQLite
    sections_data = []
    students_data = []
    faculty_data = []
    rooms_data = []
    schedules_data = []
    
    # Get Sections
    cursor = sqlite_conn.execute('SELECT id, section_name, course, year_level FROM section')
    for row in cursor:
        sections_data.append({
            'id': row['id'],
            'section_name': row['section_name'],
            'course': row['course'],
            'year_level': row['year_level']
        })
    
    # Get Students
    cursor = sqlite_conn.execute('SELECT id, student_number, name, course, year_level, section_id FROM student')
    for row in cursor:
        students_data.append({
            'id': row['id'],
            'student_number': row['student_number'],
            'name': row['name'],
            'course': row['course'],
            'year_level': row['year_level'],
            'section_id': row['section_id']
        })
    
    # Get Faculty
    cursor = sqlite_conn.execute('SELECT id, faculty_id, name, department FROM faculty')
    for row in cursor:
        faculty_data.append({
            'id': row['id'],
            'faculty_id': row['faculty_id'],
            'name': row['name'],
            'department': row['department']
        })
    
    # Get Rooms
    cursor = sqlite_conn.execute('SELECT id, room_name FROM room')
    for row in cursor:
        rooms_data.append({
            'id': row['id'],
            'room_name': row['room_name']
        })
    
    # Get Schedules
    cursor = sqlite_conn.execute('SELECT id, time, day, subject, section_id, faculty_id, room_id FROM schedule')
    for row in cursor:
        schedules_data.append({
            'id': row['id'],
            'time': row['time'],
            'day': row['day'],
            'subject': row['subject'],
            'section_id': row['section_id'],
            'faculty_id': row['faculty_id'],
            'room_id': row['room_id']
        })
    
    sqlite_conn.close()
    
    # Insert data into MySQL using SQLAlchemy models
    with app.app_context():
        # Insert sections
        for section in sections_data:
            db.session.add(Section(
                id=section['id'],
                section_name=section['section_name'],
                course=section['course'],
                year_level=section['year_level']
            ))
        db.session.commit()
        
        # Insert faculty
        for faculty in faculty_data:
            db.session.add(Faculty(
                id=faculty['id'],
                faculty_id=faculty['faculty_id'],
                name=faculty['name'],
                department=faculty['department']
            ))
        db.session.commit()
        
        # Insert rooms
        for room in rooms_data:
            db.session.add(Room(
                id=room['id'],
                room_name=room['room_name']
            ))
        db.session.commit()
        
        # Insert students
        for student in students_data:
            db.session.add(Student(
                id=student['id'],
                student_number=student['student_number'],
                name=student['name'],
                course=student['course'],
                year_level=student['year_level'],
                section_id=student['section_id']
            ))
        db.session.commit()
        
        # Insert schedules
        for schedule in schedules_data:
            db.session.add(Schedule(
                id=schedule['id'],
                time=schedule['time'],
                day=schedule['day'],
                subject=schedule['subject'],
                section_id=schedule['section_id'],
                faculty_id=schedule['faculty_id'],
                room_id=schedule['room_id']
            ))
        db.session.commit()
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    # Create MySQL database
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password=''
    )
    conn.cursor().execute('CREATE DATABASE IF NOT EXISTS ccs_info')
    conn.close()
    
    # Run migration
    migrate_from_sqlite_to_mysql()