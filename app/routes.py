from flask import render_template, request, redirect, url_for, jsonify
from app import app, db
from app.models import Student, Faculty, Section, Schedule, Room  # Make sure Room is included here
from sqlalchemy import or_

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/students/search')
def search_students():
    query = request.args.get('q', '')
    if len(query) >= 2:
        students = Student.query.filter(
            Student.name.ilike(f'%{query}%') | 
            Student.student_number.ilike(f'%{query}%')
        ).limit(10).all()
        return jsonify([{
            'id': student.student_id,  # Changed from student.id to student.student_id
            'name': student.name,
            'student_number': student.student_number
        } for student in students])
    return jsonify([])

@app.route('/api/faculty/search')
def faculty_search_api():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    faculty_members = Faculty.query.filter(
        or_(
            Faculty.name.ilike(f'%{query}%'),
            Faculty.faculty_id.ilike(f'%{query}%'),
            Faculty.department.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = [{'id': f.faculty_id, 'name': f.name, 'department': f.department} for f in faculty_members]
    return jsonify(results)

@app.route('/api/rooms/search')
def room_search_api():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    rooms = Room.query.filter(
        Room.room_name.ilike(f'%{query}%')
    ).limit(10).all()
    
    results = [{'room_id': r.room_id, 'room_name': r.room_name} for r in rooms]
    return jsonify(results)


@app.route('/api/sections/search')
def section_search_api():
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    sections = Section.query.filter(
        or_(
            Section.section_name.ilike(f'%{query}%'),
            Section.program.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = [{'section_id': s.section_id, 'section_name': s.section_name} for s in sections]
    return jsonify(results)

@app.route('/students', methods=['GET'])
def student_list():
    search = request.args.get('search', '')
    if search:
        students = Student.query.filter(
            Student.name.ilike(f'%{search}%') | 
            Student.student_number.ilike(f'%{search}%')
        ).all()
    else:
        students = Student.query.all()
    return render_template('student_list.html', students=students)

@app.route('/faculty', methods=['GET'])
def faculty_list():
    search = request.args.get('search', '')
    if search:
        faculty = Faculty.query.filter(Faculty.name.contains(search) | 
                                    Faculty.faculty_id.contains(search)).all()
    else:
        faculty = Faculty.query.all()
    return render_template('faculty_list.html', faculty=faculty)

@app.route('/rooms')
def room_list():
    search = request.args.get('search', '')
    if search:
        rooms = Room.query.filter(Room.room_name.ilike(f'%{search}%')).all()
    else:
        rooms = Room.query.all()
    return render_template('room_list.html', rooms=rooms)


@app.route('/sections')
def section_list():
    search = request.args.get('search', '')
    if search:
        sections = Section.query.filter(
            or_(
                Section.section_name.ilike(f'%{search}%'),
                Section.program.ilike(f'%{search}%')
            )
        ).all()
    else:
        sections = Section.query.all()
    return render_template('section_list.html', sections=sections)

@app.route('/student/<int:student_id>')
def student_profile(student_id):
    student = Student.query.get_or_404(student_id)
    schedules = Schedule.query.filter_by(section_id=student.section_id).all()
    return render_template('student_profile.html', student=student, schedules=schedules)

@app.route('/faculty/<int:faculty_id>')
def faculty_profile(faculty_id):
    faculty = Faculty.query.get_or_404(faculty_id)
    schedules = Schedule.query.filter_by(faculty_id=faculty_id).all()
    return render_template('faculty_profile.html', faculty=faculty, schedules=schedules)

@app.route('/section/<int:section_id>')
def section_profile(section_id):
    section = Section.query.get_or_404(section_id)
    students = Student.query.filter_by(section_id=section_id).all()
    schedules = Schedule.query.filter_by(section_id=section_id).all()
    return render_template('section_profile.html', section=section, students=students, schedules=schedules)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    return render_template('admin_login.html')

@app.route('/room/login', methods=['GET', 'POST'])
def room_login():
    return render_template('room_login.html')

@app.route('/pc-tracking')
def pc_tracking():
    return render_template('pc_tracking.html')

@app.route('/submit-documents')
def submit_documents():
    return render_template('submit_documents.html')

@app.route('/room/<int:room_id>')
def room_profile(room_id):
    # Get the room by ID or return 404 if not found
    room = Room.query.get_or_404(room_id)
    
    # Get all schedules that use this room
    schedules = Schedule.query.filter_by(room_id=room_id).all()
    
    return render_template('room_profile.html', room=room, schedules=schedules)
