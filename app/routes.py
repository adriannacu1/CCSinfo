from flask import render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from datetime import datetime, timedelta
import hashlib
import time

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Your MySQL password
    'database': 'ccs_info',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """Get database connection with optimized settings"""
    try:
        connection = mysql.connector.connect(
            **DB_CONFIG,
            autocommit=True,
            use_unicode=True,
            buffered=True
        )
        return connection
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def verify_admin_password(stored_password, provided_password):
    """Verify admin password (optimized)"""
    from app import bcrypt
    
    stored_password = stored_password.strip()
    provided_password = provided_password.strip()
    
    # Check bcrypt hash first
    if stored_password.startswith(('$2b$', '$2a$', '$2y$')):
        try:
            return bcrypt.check_password_hash(stored_password, provided_password)
        except:
            return False
    
    # Direct comparison
    return stored_password == provided_password

def register_routes(app):
    """Register all routes with the app"""
    
    @app.route('/')
    def index():
        return render_template('index.html')

    # ==================== ROOM LOGIN ROUTES ====================
    
    @app.route('/room/login')
    def room_login():
        """Room login page"""
        return render_template('room_login.html')
    
    @app.route('/room/logout')
    def room_logout():
        """Room logout page"""
        return render_template('room_logout.html')

    # ==================== ADMIN ROUTES ====================
    
    @app.route('/admin/login', methods=['GET', 'POST'])
    def admin_login():
        print(f"=== ADMIN LOGIN ROUTE ACCESSED ===")
        print(f"Request method: {request.method}")
        print(f"URL: {request.url}")
        
        if request.method == 'POST':
            print(f"=== POST REQUEST RECEIVED ===")
            print(f"Form data keys: {list(request.form.keys())}")
            print(f"Raw form data: {dict(request.form)}")
            
            # Get form data
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            remember = request.form.get('remember')
            
            print(f"Parsed username: '{username}' (length: {len(username)})")
            print(f"Parsed password: '{password}' (length: {len(password)})")
            print(f"Remember me: {remember}")
            
            # Validate input
            if not username or not password:
                error_msg = 'Please enter both username and password'
                print(f"VALIDATION ERROR: {error_msg}")
                flash(error_msg, 'error')
                return render_template('admin/login.html')
            
            # Database connection
            print(f"=== DATABASE CONNECTION ===")
            conn = get_db_connection()
            if not conn:
                error_msg = 'Database connection failed'
                print(f"DATABASE ERROR: {error_msg}")
                flash(error_msg, 'error')
                return render_template('admin/login.html')
            
            try:
                cursor = conn.cursor(dictionary=True)
                
                # Query user
                query = "SELECT admin_id, username, password, full_name, email, role, is_active FROM admin WHERE username = %s"
                print(f"Executing query: {query}")
                print(f"With parameter: '{username}'")
                
                cursor.execute(query, (username,))
                admin = cursor.fetchone()
                
                print(f"Database result: {admin}")
                
                if not admin:
                    print(f"USER NOT FOUND: No admin with username '{username}'")
                    flash('Invalid username or password', 'error')
                    cursor.close()
                    conn.close()
                    return render_template('admin/login.html')
                
                # Check if account is active
                if not admin.get('is_active', 0):
                    print(f"ACCOUNT INACTIVE: User '{username}' is not active")
                    flash('Account is deactivated. Contact administrator.', 'error')
                    cursor.close()
                    conn.close()
                    return render_template('admin/login.html')
                
                # Verify password
                stored_password = admin.get('password', '')
                print(f"=== PASSWORD VERIFICATION ===")
                print(f"Stored password: '{stored_password}' (length: {len(stored_password)})")
                print(f"Provided password: '{password}' (length: {len(password)})")
                
                password_valid = verify_admin_password(stored_password, password)
                print(f"Password verification result: {password_valid}")
                
                if not password_valid:
                    print(f"PASSWORD MISMATCH for user '{username}'")
                    flash('Invalid username or password', 'error')
                    cursor.close()
                    conn.close()
                    return render_template('admin/login.html')
                
                # Login successful
                print(f"=== LOGIN SUCCESSFUL ===")
                print(f"User '{username}' authenticated successfully")
                
                # Set session data
                session.permanent = bool(remember)
                session['admin_id'] = admin['admin_id']
                session['admin_username'] = admin['username']
                session['admin_role'] = admin['role']
                session['admin_name'] = admin['full_name']
                
                print(f"Session data set: {dict(session)}")
                
                # Update last login
                update_query = "UPDATE admin SET last_login = NOW() WHERE admin_id = %s"
                cursor.execute(update_query, (admin['admin_id'],))
                conn.commit()
                
                cursor.close()
                conn.close()
                
                flash(f'Welcome back, {admin["full_name"]}!', 'success')
                
                # Redirect to admin dashboard
                print(f"Redirecting to admin dashboard...")
                return redirect(url_for('admin_dashboard'))  # Make sure this matches the route name
                
            except Exception as e:
                print(f"=== EXCEPTION OCCURRED ===")
                print(f"Error: {str(e)}")
                print(f"Error type: {type(e).__name__}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                
                flash('An error occurred during login. Please try again.', 'error')
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
                return render_template('admin/login.html')
        
        # GET request - show login form
        print(f"=== SHOWING LOGIN FORM ===")
        return render_template('admin/login.html')

    @app.route('/admin/dashboard')
    def admin_dashboard():
        """Admin dashboard with authentication check"""
        print(f"=== ADMIN DASHBOARD ACCESSED ===")
        
        # Check if user is logged in
        if 'admin_id' not in session:
            print("No admin session found, redirecting to login")
            flash('Please log in to access the admin dashboard', 'error')
            return redirect(url_for('admin_login'))
        
        print(f"Admin session found: {dict(session)}")
        
        # Get admin info from session
        admin_info = {
            'admin_id': session.get('admin_id'),
            'username': session.get('admin_username'),
            'full_name': session.get('admin_name', 'Administrator'),
            'role': session.get('admin_role', 'admin')
        }
        
        # Get database statistics
        conn = get_db_connection()
        stats = {
            'total_students': 0,
            'active_students': 0,
            'total_faculty': 0,
            'active_faculty': 0,
            'total_rooms': 0,
            'available_rooms': 0,
            'total_sections': 0,
            'active_sections': 0
        }
        
        if conn:
            try:
                cursor = conn.cursor()
                
                # Count students
                cursor.execute("SELECT COUNT(*) FROM students")
                stats['total_students'] = cursor.fetchone()[0] or 0
                stats['active_students'] = stats['total_students']
                
                # Count faculty
                cursor.execute("SELECT COUNT(*) FROM faculty")
                stats['total_faculty'] = cursor.fetchone()[0] or 0
                stats['active_faculty'] = stats['total_faculty']
                
                # Count rooms
                cursor.execute("SELECT COUNT(*) FROM rooms")
                stats['total_rooms'] = cursor.fetchone()[0] or 0
                stats['available_rooms'] = stats['total_rooms']
                
                # Count sections
                cursor.execute("SELECT COUNT(*) FROM sections")
                stats['total_sections'] = cursor.fetchone()[0] or 0
                stats['active_sections'] = stats['total_sections']
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Error getting stats: {e}")
        
        recent_students = []
        recent_faculty = []
        
        return render_template('admin/dashboard.html', 
                         admin=admin_info, 
                         stats=stats,
                         recent_students=recent_students,
                         recent_faculty=recent_faculty)

    @app.route('/admin/students', methods=['GET', 'POST'])
    def admin_students():
        """Admin students management with CRUD operations"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin_info = {
            'admin_id': session.get('admin_id'),
            'username': session.get('admin_username'),
            'full_name': session.get('admin_name', 'Administrator'),
            'role': session.get('admin_role', 'admin')
        }
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            conn = get_db_connection()
            if not conn:
                flash('Database connection failed', 'error')
                return redirect(url_for('admin_students'))
            
            try:
                cursor = conn.cursor()
                
                if action == 'add':
                    # Add new student
                    student_number = request.form.get('student_number')
                    name = request.form.get('name')
                    course = request.form.get('course')
                    year_level = request.form.get('year_level')
                    section_id = request.form.get('section_id')
                    email = request.form.get('email') or None
                    status = 'Active'
                    
                    # Get course_id based on course name
                    cursor.execute("SELECT course_id FROM courses WHERE course_name = %s", (course,))
                    course_result = cursor.fetchone()
                    course_id = course_result[0] if course_result else None
                    
                    # Check if student number already exists
                    cursor.execute("SELECT student_id FROM students WHERE student_number = %s", (student_number,))
                    if cursor.fetchone():
                        flash(f'Student Number {student_number} already exists', 'error')
                    else:
                        cursor.execute("""
                            INSERT INTO students (student_number, name, course, year_level, section_id, email, status, course_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        """, (student_number, name, course, year_level, section_id, email, status, course_id))
                        conn.commit()
                        flash(f'Student {name} added successfully', 'success')
                
                elif action == 'edit':
                    # Edit existing student
                    student_id = request.form.get('student_id_hidden')
                    student_number = request.form.get('student_number')
                    name = request.form.get('name')
                    course = request.form.get('course')
                    year_level = request.form.get('year_level')
                    section_id = request.form.get('section_id')
                    email = request.form.get('email') or None
                    
                    # Get course_id based on course name
                    cursor.execute("SELECT course_id FROM courses WHERE course_name = %s", (course,))
                    course_result = cursor.fetchone()
                    course_id = course_result[0] if course_result else None
                    
                    # Check if new student number conflicts with existing ones (except current)
                    cursor.execute("SELECT student_id FROM students WHERE student_number = %s AND student_id != %s", (student_number, student_id))
                    if cursor.fetchone():
                        flash(f'Student Number {student_number} already exists', 'error')
                    else:
                        cursor.execute("""
                            UPDATE students SET student_number = %s, name = %s, course = %s, 
                            year_level = %s, section_id = %s, email = %s, course_id = %s
                            WHERE student_id = %s
                        """, (student_number, name, course, year_level, section_id, email, course_id, student_id))
                        conn.commit()
                        flash(f'Student {name} updated successfully', 'success')
                
                elif action == 'delete':
                    # Delete student
                    student_id = request.form.get('student_id_hidden')
                    cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
                    conn.commit()
                    flash('Student deleted successfully', 'success')
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
        
            return redirect(url_for('admin_students'))
        
        # GET request - fetch and display students
        students = []
        sections = []
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                
                # Get students with section information
                cursor.execute("""
                    SELECT s.student_id, s.student_number, s.name, s.course, s.year_level, 
                           s.email, s.status, s.section_id,
                           sec.section_name
                    FROM students s
                    LEFT JOIN sections sec ON s.section_id = sec.section_id
                    ORDER BY s.student_id DESC
                """)
                students = cursor.fetchall()
                
                # Get all sections for the dropdown
                cursor.execute("""
                    SELECT section_id, section_name, course, year_level
                    FROM sections
                    ORDER BY course, year_level, section_name
                """)
                sections = cursor.fetchall()
                
                cursor.close()
                conn.close()
            except Exception as e:
                flash(f'Error fetching students: {str(e)}', 'error')
        
        return render_template('admin/students.html', admin=admin_info, students=students, sections=sections)

    @app.route('/admin/faculty', methods=['GET', 'POST'])
    def admin_faculty():
        """Admin faculty management with CRUD operations"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin_info = {
            'admin_id': session.get('admin_id'),
            'username': session.get('admin_username'),
            'full_name': session.get('admin_name', 'Administrator'),
            'role': session.get('admin_role', 'admin')
        }
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            conn = get_db_connection()
            if not conn:
                flash('Database connection failed', 'error')
                return redirect(url_for('admin_faculty'))
            
            try:
                cursor = conn.cursor()
                
                if action == 'add':
                    # Add new faculty - matching your database schema
                    name = request.form.get('name')
                    department = request.form.get('department')
                    username = request.form.get('username') or f"fac{int(time.time())}"  # Generate if not provided
                    password = request.form.get('password') or '12345'  # Default password
                    
                    cursor.execute("""
                        INSERT INTO faculty (name, department, username, password)
                        VALUES (%s, %s, %s, %s)
                    """, (name, department, username, password))
                    conn.commit()
                    flash(f'Faculty member {name} added successfully', 'success')
                
                elif action == 'edit':
                    # Edit existing faculty
                    faculty_id = request.form.get('faculty_id_hidden')
                    name = request.form.get('name')
                    department = request.form.get('department')
                    username = request.form.get('username')
                    password = request.form.get('password')
                    
                    cursor.execute("""
                        UPDATE faculty SET name = %s, department = %s, username = %s, password = %s
                        WHERE faculty_id = %s
                    """, (name, department, username, password, faculty_id))
                    conn.commit()
                    flash(f'Faculty member {name} updated successfully', 'success')
                
                elif action == 'delete':
                    # Delete faculty
                    faculty_id = request.form.get('faculty_id_hidden')
                    cursor.execute("DELETE FROM faculty WHERE faculty_id = %s", (faculty_id,))
                    conn.commit()
                    flash('Faculty member deleted successfully', 'success')
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
            
            return redirect(url_for('admin_faculty'))
        
        # GET request - fetch and display faculty
        faculty = []
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM faculty ORDER BY name")
                faculty = cursor.fetchall()
                cursor.close()
                conn.close()
            except Exception as e:
                flash(f'Error fetching faculty: {str(e)}', 'error')
        
        return render_template('admin/faculty.html', admin=admin_info, faculty=faculty)

    @app.route('/admin/rooms', methods=['GET', 'POST'])
    def admin_rooms():
        """Admin rooms management with CRUD operations"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin_info = {
            'admin_id': session.get('admin_id'),
            'username': session.get('admin_username'),
            'full_name': session.get('admin_name', 'Administrator'),
            'role': session.get('admin_role', 'admin')
        }
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            conn = get_db_connection()
            if not conn:
                flash('Database connection failed', 'error')
                return redirect(url_for('admin_rooms'))
            
            try:
                cursor = conn.cursor()
                
                if action == 'add':
                    # Add new room - matching your database schema
                    room_name = request.form.get('room_name')
                    floor = request.form.get('floor') or None
                    capacity = request.form.get('capacity') or None
                    
                    # Check if room name already exists
                    cursor.execute("SELECT room_id FROM rooms WHERE room_name = %s", (room_name,))
                    if cursor.fetchone():
                        flash(f'Room {room_name} already exists', 'error')
                    else:
                        cursor.execute("""
                            INSERT INTO rooms (room_name, floor, capacity)
                            VALUES (%s, %s, %s)
                        """, (room_name, floor, capacity))
                        conn.commit()
                        flash(f'Room {room_name} added successfully', 'success')
                
                elif action == 'edit':
                    # Edit existing room
                    room_id = request.form.get('room_id_hidden')
                    room_name = request.form.get('room_name')
                    floor = request.form.get('floor') or None
                    capacity = request.form.get('capacity') or None
                    
                    # Check if new room name conflicts with existing ones (except current)
                    cursor.execute("SELECT room_id FROM rooms WHERE room_name = %s AND room_id != %s", (room_name, room_id))
                    if cursor.fetchone():
                        flash(f'Room name {room_name} already exists', 'error')
                    else:
                        cursor.execute("""
                            UPDATE rooms SET room_name = %s, floor = %s, capacity = %s
                            WHERE room_id = %s
                        """, (room_name, floor, capacity, room_id))
                        conn.commit()
                        flash(f'Room {room_name} updated successfully', 'success')
                
                elif action == 'delete':
                    # Delete room
                    room_id = request.form.get('room_id_hidden')
                    cursor.execute("DELETE FROM rooms WHERE room_id = %s", (room_id,))
                    conn.commit()
                    flash('Room deleted successfully', 'success')
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
            
            return redirect(url_for('admin_rooms'))
        
        # GET request - fetch and display rooms
        rooms = []
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM rooms ORDER BY room_name")
                rooms = cursor.fetchall()
                cursor.close()
                conn.close()
            except Exception as e:
                flash(f'Error fetching rooms: {str(e)}', 'error')
        
        return render_template('admin/rooms.html', admin=admin_info, rooms=rooms)

    @app.route('/admin/sections', methods=['GET', 'POST'])
    def admin_sections():
        """Admin sections management with CRUD operations"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin_info = {
            'admin_id': session.get('admin_id'),
            'username': session.get('admin_username'),
            'full_name': session.get('admin_name', 'Administrator'),
            'role': session.get('admin_role', 'admin')
        }
        
        if request.method == 'POST':
            action = request.form.get('action')
            
            conn = get_db_connection()
            if not conn:
                flash('Database connection failed', 'error')
                return redirect(url_for('admin_sections'))
            
            try:
                cursor = conn.cursor()
                
                if action == 'add':
                    # Add new section - matching your database schema
                    section_name = request.form.get('section_name')
                    course = request.form.get('course')
                    year_level = request.form.get('year_level')
                    
                    # Get course_id based on course name
                    cursor.execute("SELECT course_id FROM courses WHERE course_name = %s", (course,))
                    course_result = cursor.fetchone()
                    course_id = course_result[0] if course_result else None
                    
                    # Check if section name already exists for same course and year
                    cursor.execute("""
                        SELECT section_id FROM sections 
                        WHERE section_name = %s AND course = %s AND year_level = %s
                    """, (section_name, course, year_level))
                    if cursor.fetchone():
                        flash(f'Section {section_name} already exists for {course} Year {year_level}', 'error')
                    else:
                        cursor.execute("""
                            INSERT INTO sections (section_name, course, year_level, course_id)
                            VALUES (%s, %s, %s, %s)
                        """, (section_name, course, year_level, course_id))
                        conn.commit()
                        flash(f'Section {section_name} added successfully', 'success')
                
                elif action == 'edit':
                    # Edit existing section
                    section_id = request.form.get('section_id_hidden')
                    section_name = request.form.get('section_name')
                    course = request.form.get('course')
                    year_level = request.form.get('year_level')
                    
                    # Get course_id based on course name
                    cursor.execute("SELECT course_id FROM courses WHERE course_name = %s", (course,))
                    course_result = cursor.fetchone()
                    course_id = course_result[0] if course_result else None
                    
                    # Check if new section name conflicts (except current)
                    cursor.execute("""
                        SELECT section_id FROM sections 
                        WHERE section_name = %s AND course = %s AND year_level = %s AND section_id != %s
                    """, (section_name, course, year_level, section_id))
                    if cursor.fetchone():
                        flash(f'Section {section_name} already exists for {course} Year {year_level}', 'error')
                    else:
                        cursor.execute("""
                            UPDATE sections SET section_name = %s, course = %s, year_level = %s, course_id = %s
                            WHERE section_id = %s
                        """, (section_name, course, year_level, course_id, section_id))
                        conn.commit()
                        flash(f'Section {section_name} updated successfully', 'success')
                
                elif action == 'delete':
                    # Delete section
                    section_id = request.form.get('section_id_hidden')
                    cursor.execute("DELETE FROM sections WHERE section_id = %s", (section_id,))
                    conn.commit()
                    flash('Section deleted successfully', 'success')
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'error')
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
            
            return redirect(url_for('admin_sections'))
        
        # GET request - fetch and display sections
        sections = []
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                
                # Get sections with student count
                cursor.execute("""
                    SELECT s.*,
                           (SELECT COUNT(*) FROM students st WHERE st.section_id = s.section_id) as student_count
                    FROM sections s
                    ORDER BY s.course, s.year_level, s.section_name
                """)
                sections = cursor.fetchall()
                
                cursor.close()
                conn.close()
            except Exception as e:
                flash(f'Error fetching sections: {str(e)}', 'error')
        
        return render_template('admin/sections.html', admin=admin_info, sections=sections)

    # ==================== OTHER ROUTES ====================
    
    @app.route('/students')
    def student_list():
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return render_template('student/list.html', students=[])
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get all students with course and section info
            students_query = """
            SELECT s.student_id, s.student_number, s.name, s.course, s.year_level, s.email,
                   sec.section_name, sec.section_id
            FROM students s
            LEFT JOIN sections sec ON s.section_id = sec.section_id
            ORDER BY s.name
            """
            cursor.execute(students_query)
            students = cursor.fetchall()
            
            return render_template('student/list.html', students=students)
            
        except mysql.connector.Error as e:
            flash(f'Error loading students: {e}', 'error')
            return render_template('student/list.html', students=[])
        finally:
            cursor.close()
            conn.close()

    @app.route('/student/<int:student_id>')
    def student_profile(student_id):
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return redirect(url_for('student_list'))
        
        try:
            cursor = conn.cursor(dictionary=True)
            # Get student info with section and course
            cursor.execute('''
                SELECT s.*, sec.section_name, sec.year_level, c.course_name
                FROM students s
                LEFT JOIN sections sec ON s.section_id = sec.section_id
                LEFT JOIN courses c ON s.course_id = c.course_id
                WHERE s.student_id = %s
            ''', (student_id,))
            student = cursor.fetchone()            
            if not student:
                flash('Student not found', 'error')
                return redirect(url_for('student_list'))
            
            # Get schedule/subjects for the student's section (with subject, instructor, room)
            cursor.execute('''
                SELECT sch.time, sch.day, sub.subject_name, f.name AS instructor_name, r.room_name
                FROM schedule sch
                LEFT JOIN subjects sub ON sch.subject_id = sub.subject_id
                LEFT JOIN faculty f ON sch.faculty_id = f.faculty_id
                LEFT JOIN rooms r ON sch.room_id = r.room_id
                WHERE sch.section_id = %s
            ''', (student['section_id'],))
            schedule = cursor.fetchall()
            
            return render_template('student/profile.html', student=student, schedule=schedule)
        except mysql.connector.Error as e:
            flash(f'Error loading student: {e}', 'error')
            return redirect(url_for('student_list'))
        finally:
            cursor.close()
            conn.close()

    @app.route('/faculty')
    def faculty_list():
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return render_template('faculty/list.html', faculty=[])
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM faculty ORDER BY name")
            faculty = cursor.fetchall()
            
            return render_template('faculty/list.html', faculty=faculty)
            
        except mysql.connector.Error as e:
            flash(f'Error loading faculty: {e}', 'error')
            return render_template('faculty/list.html', faculty=[])
        finally:
            cursor.close()
            conn.close()

    @app.route('/faculty/<int:faculty_id>')
    def faculty_profile(faculty_id):
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return redirect(url_for('faculty_list'))
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get faculty info
            cursor.execute("SELECT * FROM faculty WHERE faculty_id = %s", (faculty_id,))
            faculty = cursor.fetchone()
            
            if not faculty:
                flash('Faculty member not found', 'error')
                return redirect(url_for('faculty_list'))
            
            return render_template('faculty/profile.html', faculty=faculty)
            
        except mysql.connector.Error as e:
            flash(f'Error loading faculty: {e}', 'error')
            return redirect(url_for('faculty_list'))
        finally:
            cursor.close()
            conn.close()

    @app.route('/rooms')
    def room_list():
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return render_template('room/list.html', rooms=[])
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM rooms ORDER BY room_name")
            rooms = cursor.fetchall()
            
            return render_template('room/list.html', rooms=rooms)
            
        except mysql.connector.Error as e:
            flash(f'Error loading rooms: {e}', 'error')
            return render_template('room/list.html', rooms=[])
        finally:
            cursor.close()
            conn.close()

    @app.route('/room/<int:room_id>')
    def room_profile(room_id):
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return redirect(url_for('room_list'))
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get room info
            cursor.execute("SELECT * FROM rooms WHERE room_id = %s", (room_id,))
            room = cursor.fetchone()
            
            if not room:
                flash('Room not found', 'error')
                return redirect(url_for('room_list'))
            
            return render_template('room/profile.html', room=room)
            
        except mysql.connector.Error as e:
            flash(f'Error loading room: {e}', 'error')
            return redirect(url_for('room_list'))
        finally:
            cursor.close()
            conn.close()

    @app.route('/sections')
    def section_list():
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return render_template('section/list.html', sections=[])
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get all sections with course info and student count
            sections_query = """
            SELECT s.section_id, s.section_name, s.course, s.year_level,
                   (SELECT COUNT(*) FROM students st WHERE st.section_id = s.section_id) as student_count
            FROM sections s
            ORDER BY s.course, s.year_level, s.section_name
            """
            cursor.execute(sections_query)
            sections = cursor.fetchall()
            
            return render_template('section/list.html', sections=sections)
            
        except mysql.connector.Error as e:
            flash(f'Error loading sections: {e}', 'error')
            return render_template('section/list.html', sections=[])
        finally:
            cursor.close()
            conn.close()

    @app.route('/section/<int:section_id>')
    def section_profile(section_id):
        conn = get_db_connection()
        if not conn:
            flash('Database connection error', 'error')
            return redirect(url_for('section_list'))
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get section info
            cursor.execute("SELECT * FROM sections WHERE section_id = %s", (section_id,))
            section = cursor.fetchone()
            
            if not section:
                flash('Section not found', 'error')
                return redirect(url_for('section_list'))
            
            # Get students in this section
            cursor.execute("""
                SELECT student_id, student_number, name
                FROM students
                WHERE section_id = %s
                ORDER BY name
            """, (section_id,))
            students = cursor.fetchall()
            
            return render_template('section/profile.html', section=section, students=students)
            
        except mysql.connector.Error as e:
            flash(f'Error loading section: {e}', 'error')
            return redirect(url_for('section_list'))
        finally:
            cursor.close()
            conn.close()

    # PC Tracking route (the one causing the error)
    @app.route('/pc-tracking')
    def pc_tracking():
        """PC Tracking page - placeholder for now"""
        return render_template('pc_tracking.html')

    # Schedules route
    @app.route('/schedules')
    def schedules():
        """Schedules page - placeholder for now"""
        return render_template('schedules.html')

    # About route
    @app.route('/about')
    def about():
        """About page"""
        return render_template('about.html')

    # Contact route  
    @app.route('/contact')
    def contact():
        """Contact page"""
        return render_template('contact.html')

    @app.route('/admin/logout')
    def admin_logout():
        """Admin logout"""
        session.clear()
        flash('You have been logged out successfully', 'success')
        return redirect(url_for('index'))

    @app.route('/admin/settings')
    def admin_settings():
        return render_template('admin/settings.html')
    
    @app.route('/admin/faculty/<int:faculty_id>')
    def admin_faculty_profile(faculty_id):
        """View faculty profile with schedules and activity log"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))

        conn = get_db_connection()
        if not conn:
            flash('Database connection failed', 'error')
            return redirect(url_for('admin_faculty'))

        try:
            cursor = conn.cursor(dictionary=True)

            # Fetch faculty details
            cursor.execute("""
                SELECT f.*, 
                       CASE 
                           WHEN f.status = 1 THEN 'Active'
                           ELSE 'Inactive'
                       END as status_state
                FROM faculty f
                WHERE f.faculty_id = %s
            """, (faculty_id,))
            faculty = cursor.fetchone()

            if not faculty:
                flash('Faculty not found', 'error')
                return redirect(url_for('admin_faculty'))

            # Fetch faculty schedules with subject, section and room details
            cursor.execute("""
                SELECT s.*, 
                       sec.section_name,
                       sub.subject_code,
                       sub.subject_name as subject,
                       r.room_name,
                       CONCAT(s.start_time, ' - ', s.end_time) as time
                FROM schedules s
                LEFT JOIN sections sec ON s.section_id = sec.section_id
                LEFT JOIN subjects sub ON s.subject_id = sub.subject_id
                LEFT JOIN rooms r ON s.room_id = r.room_id
                WHERE s.faculty_id = %s
                ORDER BY FIELD(s.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
                         s.start_time
            """, (faculty_id,))
            schedules = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template('admin/faculty_profile.html', 
                                faculty=faculty,
                                schedules=schedules)

        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return redirect(url_for('admin_faculty'))

    @app.route('/admin/room/<int:room_id>')
    def admin_room_profile(room_id):
        """View room profile with schedules and stats"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))

        conn = get_db_connection()
        if not conn:
            flash('Database connection failed', 'error')
            return redirect(url_for('admin_rooms'))

        try:
            cursor = conn.cursor(dictionary=True)

            # Fetch room details
            cursor.execute("""
                SELECT * FROM rooms WHERE room_id = %s
            """, (room_id,))
            room = cursor.fetchone()

            if not room:
                flash('Room not found', 'error')
                return redirect(url_for('admin_rooms'))

            # Fetch room schedules with subject, section and faculty details
            cursor.execute("""
                SELECT s.*, 
                       sec.section_name,
                       sub.subject_code,
                       sub.subject_name as subject,
                       f.name as faculty_name,
                       CONCAT(s.start_time, ' - ', s.end_time) as time
                FROM schedules s
                LEFT JOIN sections sec ON s.section_id = sec.section_id
                LEFT JOIN subjects sub ON s.subject_id = sub.subject_id
                LEFT JOIN faculty f ON s.faculty_id = f.faculty_id
                WHERE s.room_id = %s
                ORDER BY FIELD(s.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
                         s.start_time
            """, (room_id,))
            schedules = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template('admin/room_profile.html', 
                                room=room,
                                schedules=schedules)

        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return redirect(url_for('admin_rooms'))

    @app.route('/admin/section/<int:section_id>')
    def admin_section_profile(section_id):
        """View section profile with student list, schedule, and course info"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))

        conn = get_db_connection()
        if not conn:
            flash('Database connection failed', 'error')
            return redirect(url_for('admin_sections'))

        try:
            cursor = conn.cursor(dictionary=True)

            # Fetch section details with course info
            cursor.execute("""
                SELECT s.*,
                       c.course_name as course
                FROM sections s
                LEFT JOIN courses c ON s.course_id = c.course_id
                WHERE s.section_id = %s
            """, (section_id,))
            section = cursor.fetchone()

            if not section:
                flash('Section not found', 'error')
                return redirect(url_for('admin_sections'))

            # Fetch students in this section
            cursor.execute("""
                SELECT s.student_id,
                       s.student_number,
                       s.name,
                       s.email,
                       s.status
                FROM students s
                WHERE s.section_id = %s
                ORDER BY s.name
            """, (section_id,))
            students = cursor.fetchall()

            # Fetch section schedules with subject, faculty and room details
            cursor.execute("""
                SELECT s.*, 
                       sub.subject_code,
                       sub.subject_name as subject,
                       f.name as faculty_name,
                       r.room_name,
                       CONCAT(s.start_time, ' - ', s.end_time) as time
                FROM schedules s
                LEFT JOIN subjects sub ON s.subject_id = sub.subject_id
                LEFT JOIN faculty f ON s.faculty_id = f.faculty_id
                LEFT JOIN rooms r ON s.room_id = r.room_id
                WHERE s.section_id = %s
                ORDER BY FIELD(s.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
                         s.start_time
            """, (section_id,))
            schedules = cursor.fetchall()

            cursor.close()
            conn.close()

            return render_template('admin/section_profile.html',
                                section=section,
                                students=students,
                                schedules=schedules)

        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return redirect(url_for('admin_sections'))

    @app.route('/admin/students/<int:student_id>/profile')
    def admin_student_profile_api(student_id):
        """API endpoint to get student profile data for modal"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor(dictionary=True)
              # Get student info with section and course
            cursor.execute('''
                SELECT s.*, 
                       sec.section_name, 
                       sec.year_level, 
                       c.course_name
                FROM students s
                LEFT JOIN sections sec ON s.section_id = sec.section_id
                LEFT JOIN courses c ON s.course_id = c.course_id
                WHERE s.student_id = %s
            ''', (student_id,))
            student = cursor.fetchone()
            
            if not student:
                return jsonify({'success': False, 'message': 'Student not found'}), 404
              # Get student's schedule (from section)
            schedule = []
            if student.get('section_id'):
                cursor.execute('''
                    SELECT sch.day, 
                           sch.time as time_range,
                           sch.subject as subject_name, 
                           f.name AS faculty_name, 
                           r.room_name
                    FROM schedule sch
                    LEFT JOIN faculty f ON sch.faculty_id = f.faculty_id
                    LEFT JOIN rooms r ON sch.room_id = r.room_id
                    WHERE sch.section_id = %s
                    ORDER BY FIELD(sch.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
                ''', (student['section_id'],))                
                
            schedule = cursor.fetchall()
            
            # Get activity log (recent attendance) for admin use
            activity_log = []
            cursor.execute('''
                SELECT sa.*, 
                       f.name AS professor_name,
                       DATE_FORMAT(sa.check_in_time, '%Y-%m-%d %H:%i:%s') as timestamp,
                       sa.room_number as room_name,
                       sa.class_session_id as session_id
                FROM student_attendance sa
                LEFT JOIN faculty f ON sa.professor_id = f.faculty_id
                WHERE sa.student_number = %s
                ORDER BY sa.check_in_time DESC
                LIMIT 10
            ''', (student['student_number'],))
            activity_log = cursor.fetchall()
            
            cursor.close()
            conn.close()

            # Format the response
            student_data = {
                'student_id': student['student_id'],
                'name': student['name'],
                'student_number': student['student_number'],
                'email': student['email'] or 'N/A',
                'course_name': student['course_name'] or 'N/A',
                'year_level': student['year_level'] or 'N/A',
                'section_name': student['section_name'] or 'N/A',
                'status': student['status'] or 'Active',
                'schedule': schedule or [],
                'activity_log': activity_log or []
            }

            return jsonify({'success': True, 'student': student_data})

        except Exception as e:
            print(f"Error in student profile API: {str(e)}")  # Debug logging
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500

    @app.route('/admin/faculty/<int:faculty_id>/profile')
    def admin_faculty_profile_api(faculty_id):
        """API endpoint to get faculty profile data for modal"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401

        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500

        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get faculty info from faculty table
            cursor.execute('''
                SELECT faculty_id, name, department, username, password, status_state
                FROM faculty 
                WHERE faculty_id = %s
            ''', (faculty_id,))
            faculty = cursor.fetchone()
            
            if not faculty:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Faculty not found'}), 404
            
            # Get faculty's teaching schedule
            schedule = []
            cursor.execute('''
                SELECT sch.day, 
                       sch.time,
                       sch.subject, 
                       sec.section_name,
                       r.room_name
                FROM schedule sch
                LEFT JOIN sections sec ON sch.section_id = sec.section_id
                LEFT JOIN rooms r ON sch.room_id = r.room_id
                WHERE sch.faculty_id = %s
                ORDER BY FIELD(sch.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
            ''', (faculty_id,))
            raw_schedule = cursor.fetchall()
            
            # Format schedule for frontend
            for item in raw_schedule:
                schedule.append({
                    'day': item['day'] or 'N/A',
                    'time': item['time'] or 'N/A',
                    'subject': item['subject'] or 'N/A',
                    'section_name': item['section_name'] or 'N/A',
                    'room_name': item['room_name'] or 'N/A'
                })

            cursor.close()
            conn.close()            # Format the response with all faculty information
            faculty_data = {
                'faculty_id': faculty['faculty_id'],
                'name': faculty['name'] or 'N/A',
                'department': faculty['department'] or 'N/A',
                'username': faculty['username'] or 'N/A',
                'status_state': faculty['status_state'] or 'N/A',
                'schedule': schedule
            }

            return jsonify({'success': True, 'faculty': faculty_data})

        except Exception as e:
            print(f"Error in faculty profile API: {str(e)}")
            import traceback
            traceback.print_exc()
            if 'cursor' in locals():
                try:
                    cursor.close()
                except:
                    pass
            if 'conn' in locals():
                try:
                    conn.close()
                except:
                    pass
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    @app.route('/admin/students/<int:student_id>', methods=['DELETE'])
    def delete_admin_student(student_id):
        """Delete a student via AJAX"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor()
            
            # Check if student exists
            cursor.execute("SELECT name FROM students WHERE student_id = %s", (student_id,))
            student = cursor.fetchone()
            
            if not student:
                return jsonify({'success': False, 'message': 'Student not found'}), 404
            
            # Delete the student
            cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'message': f'Student {student[0]} deleted successfully'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error deleting student: {str(e)}'}), 500

    # Test endpoint for debugging
    @app.route('/admin/test-db')
    def test_db_connection():
        """Test database connection and basic queries"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
            
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Test basic student query
            cursor.execute('SELECT COUNT(*) as count FROM students')
            student_count = cursor.fetchone()
            
            # Test getting a sample student
            cursor.execute('SELECT * FROM students LIMIT 1')
            sample_student = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True, 
                'student_count': student_count['count'],
                'sample_student': sample_student
            })
            
        except Exception as e:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500    # Simple test route for student profile (using real data based on student_id)
    @app.route('/admin/students/<int:student_id>/profile-test')
    def admin_student_profile_test(student_id):
        """Test version that fetches real data based on student_id"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        conn = get_db_connection()
        if not conn:
            # Return mock data if database fails
            mock_student = {
                'student_id': student_id,
                'name': f'Student {student_id}',
                'student_number': f'224-1253{student_id}M',
                'email': f'student{student_id}@example.com',
                'course_name': 'BSCS',
                'year_level': '3',
                'section_name': '3-B',
                'status': 'Active',
                'schedule': [],
                'activity_log': []
            }
            return jsonify({'success': True, 'student': mock_student})
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get real student data based on student_id
            cursor.execute('''
                SELECT s.*, 
                       sec.section_name, 
                       sec.year_level, 
                       c.course_name
                FROM students s
                LEFT JOIN sections sec ON s.section_id = sec.section_id
                LEFT JOIN courses c ON s.course_id = c.course_id
                WHERE s.student_id = %s
            ''', (student_id,))
            student = cursor.fetchone()
            
            if not student:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': f'Student with ID {student_id} not found'}), 404
            
            # Get student's schedule
            schedule = []
            if student.get('section_id'):
                cursor.execute('''
                    SELECT sch.day, 
                           sch.time as time_range,
                           sch.subject as subject_name, 
                           f.name AS faculty_name, 
                           r.room_name
                    FROM schedule sch
                    LEFT JOIN faculty f ON sch.faculty_id = f.faculty_id
                    LEFT JOIN rooms r ON sch.room_id = r.room_id
                    WHERE sch.section_id = %s
                    ORDER BY FIELD(sch.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
                ''', (student['section_id'],))
                schedule = cursor.fetchall()

            # Get activity log for this specific student
            activity_log = []
            if student.get('student_number'):
                cursor.execute('''
                    SELECT sa.pc_number,
                           f.name AS professor_name,
                           DATE_FORMAT(sa.check_in_time, '%Y-%m-%d %H:%i:%s') as check_in_time,
                           sa.room_number as room_name,
                           sa.class_session_id as session_id
                    FROM student_attendance sa
                    LEFT JOIN faculty f ON sa.professor_id = f.faculty_id
                    WHERE sa.student_number = %s
                    ORDER BY sa.check_in_time DESC
                    LIMIT 10
                ''', (student['student_number'],))
                activity_log = cursor.fetchall()

            cursor.close()
            conn.close()

            # Format the response with real data
            student_data = {
                'student_id': student['student_id'],
                'name': student['name'],
                'student_number': student['student_number'],
                'email': student['email'] or 'N/A',
                'course_name': student['course_name'] or student.get('course', 'N/A'),
                'year_level': str(student['year_level'] or 'N/A'),
                'section_name': student['section_name'] or 'N/A',
                'status': student['status'] or 'Active',
                'schedule': schedule or [],
                'activity_log': activity_log or []
            }

            return jsonify({'success': True, 'student': student_data})
            
        except Exception as e:
            print(f"Error in student profile test API: {str(e)}")
            if 'cursor' in locals():
                try:
                    cursor.close()
                except:
                    pass
            if 'conn' in locals():
                try:
                    conn.close()
                except:
                    pass
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500    # Simple and robust endpoint for student profile
    @app.route('/admin/students/<int:student_id>/profile-simple')
    def admin_student_profile_simple(student_id):
        """Simple robust version for student profile"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get student basic info
            cursor.execute('''
                SELECT * FROM students WHERE student_id = %s
            ''', (student_id,))
            student = cursor.fetchone()
            
            if not student:
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': 'Student not found'}), 404
            
            # Get section info separately
            section_name = 'N/A'
            year_level = 'N/A'
            if student.get('section_id'):
                cursor.execute('SELECT section_name, year_level FROM sections WHERE section_id = %s', 
                             (student['section_id'],))
                section = cursor.fetchone()
                if section:
                    section_name = section['section_name']
                    year_level = str(section['year_level'])
            
            # Get course info separately
            course_name = student.get('course', 'N/A')
            if student.get('course_id'):
                cursor.execute('SELECT course_name FROM courses WHERE course_id = %s', 
                             (student['course_id'],))
                course = cursor.fetchone()
                if course:
                    course_name = course['course_name']
            
            # Get schedule separately
            schedule = []
            if student.get('section_id'):
                cursor.execute('''
                    SELECT sch.day, sch.time, sch.subject, f.name as faculty_name, r.room_name
                    FROM schedule sch
                    LEFT JOIN faculty f ON sch.faculty_id = f.faculty_id
                    LEFT JOIN rooms r ON sch.room_id = r.room_id
                    WHERE sch.section_id = %s
                ''', (student['section_id'],))
                raw_schedule = cursor.fetchall()
                
                # Format schedule for frontend
                for item in raw_schedule:
                    schedule.append({
                        'time_range': item['time'] or 'N/A',
                        'day': item['day'] or 'N/A',
                        'subject_name': item['subject'] or 'N/A',
                        'faculty_name': item['faculty_name'] or 'N/A',
                        'room_name': item['room_name'] or 'N/A'
                    })
            
            # Get activity log separately (simple query)
            activity_log = []
            if student.get('student_number'):
                cursor.execute('''
                    SELECT sa.pc_number, sa.check_in_time, sa.room_number, sa.class_session_id,
                           f.name as professor_name
                    FROM student_attendance sa
                    LEFT JOIN faculty f ON sa.professor_id = f.faculty_id
                    WHERE sa.student_number = %s
                    ORDER BY sa.check_in_time DESC
                    LIMIT 10
                ''', (student['student_number'],))
                raw_activity = cursor.fetchall()
                
                # Format activity log for frontend
                for item in raw_activity:
                    activity_log.append({
                        'pc_number': item['pc_number'] or 'N/A',
                        'professor_name': item['professor_name'] or 'N/A',
                        'check_in_time': str(item['check_in_time']) if item['check_in_time'] else 'N/A',
                        'room_name': item['room_number'] or 'N/A',
                        'session_id': item['class_session_id'] or 'N/A'
                    })

            cursor.close()
            conn.close()

            # Build response
            student_data = {
                'student_id': student['student_id'],
                'name': student['name'] or 'N/A',
                'student_number': student['student_number'] or 'N/A',
                'email': student['email'] or 'N/A',
                'course_name': course_name,
                'year_level': year_level,
                'section_name': section_name,
                'status': student['status'] or 'Active',
                'schedule': schedule,
                'activity_log': activity_log
            }

            return jsonify({'success': True, 'student': student_data})
            
        except Exception as e:
            print(f"Error in simple student profile API: {str(e)}")
            import traceback
            traceback.print_exc()
            if 'cursor' in locals():
                try:
                    cursor.close()
                except:
                    pass
            if 'conn' in locals():
                try:
                    conn.close()
                except:
                    pass
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
