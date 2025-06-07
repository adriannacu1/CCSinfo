from flask import render_template, request, redirect, url_for, session, flash
import mysql.connector
from datetime import datetime, timedelta
import hashlib

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Your MySQL password
    'database': 'ccs_info',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as e:
        print(f"Database connection error: {e}")
        return None

def verify_admin_password(stored_password, provided_password):
    """Verify admin password (handles bcrypt, MD5, and plain text)"""
    from app import bcrypt  # Import Flask-Bcrypt instance
    
    print(f"=== PASSWORD VERIFICATION ===")
    print(f"Stored: '{stored_password}' (length: {len(stored_password)})")
    print(f"Provided: '{provided_password}'")
    
    # Remove any whitespace
    stored_password = stored_password.strip()
    provided_password = provided_password.strip()
    
    # Check if it's a bcrypt hash (starts with $2b$ or $2a$ or $2y$)
    if stored_password.startswith(('$2b$', '$2a$', '$2y$')):
        try:
            # Use Flask-Bcrypt's check_password_hash method
            result = bcrypt.check_password_hash(stored_password, provided_password)
            print(f"Bcrypt verification: {result}")
            return result
        except Exception as e:
            print(f"Bcrypt error: {e}")
            return False
    
    # Direct comparison for plain text
    if stored_password == provided_password:
        print("Direct match found!")
        return True
    
    # If stored password length is 32, it might be MD5
    if len(stored_password) == 32:
        provided_hash = hashlib.md5(provided_password.encode()).hexdigest()
        print(f"Testing MD5: '{stored_password}' vs '{provided_hash}'")
        if stored_password.lower() == provided_hash.lower():
            print("MD5 match found!")
            return True
    
    # Case insensitive comparison
    if stored_password.lower() == provided_password.lower():
        print("Case insensitive match found!")
        return True
    
    print("No password match found!")
    return False

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

    @app.route('/admin/faculty')
    def admin_faculty():
        """Faculty management page placeholder"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return "Faculty Management - Coming Soon"

    @app.route('/admin/rooms')
    def admin_rooms():
        """Rooms management page placeholder"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return "Rooms Management - Coming Soon"

    @app.route('/admin/sections')
    def admin_sections():
        """Sections management page placeholder"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return "Sections Management - Coming Soon"

    @app.route('/admin/settings')
    def admin_settings():
        """Admin settings page placeholder"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        return "Admin Settings - Coming Soon"

    @app.route('/admin/logout')
    def admin_logout():
        """Admin logout"""
        session.clear()
        flash('You have been logged out successfully', 'success')
        return redirect(url_for('admin_login'))

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
            
            # Get student info
            cursor.execute("""
                SELECT s.*, sec.section_name, sec.section_id
                FROM students s
                LEFT JOIN sections sec ON s.section_id = sec.section_id
                WHERE s.student_id = %s
            """, (student_id,))
            student = cursor.fetchone()
            
            if not student:
                flash('Student not found', 'error')
                return redirect(url_for('student_list'))
            
            # Get student's schedule (if schedules table exists)
            schedules = []
            try:
                cursor.execute("""
                    SELECT sc.*, f.name as faculty_name, f.faculty_id,
                           r.room_name, r.room_id, sub.subject_name
                    FROM schedules sc
                    LEFT JOIN faculty f ON sc.faculty_id = f.faculty_id
                    LEFT JOIN rooms r ON sc.room_id = r.room_id
                    LEFT JOIN subjects sub ON sc.subject_id = sub.subject_id
                    WHERE sc.section_id = %s
                    ORDER BY sc.day, sc.time
                """, (student.get('section_id'),))
                schedules = cursor.fetchall()
            except:
                # If schedules table doesn't exist, use empty list
                schedules = []
            
            return render_template('student/profile.html', student=student, schedules=schedules)
            
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
            
            # Get faculty's schedule (if schedules table exists)
            schedules = []
            try:
                cursor.execute("""
                    SELECT sc.*, sec.section_name, sec.section_id,
                           r.room_name, r.room_id, sub.subject_name
                    FROM schedules sc
                    LEFT JOIN sections sec ON sc.section_id = sec.section_id
                    LEFT JOIN rooms r ON sc.room_id = r.room_id
                    LEFT JOIN subjects sub ON sc.subject_id = sub.subject_id
                    WHERE sc.faculty_id = %s
                    ORDER BY sc.day, sc.time
                """, (faculty_id,))
                schedules = cursor.fetchall()
            except:
                # If schedules table doesn't exist, use empty list
                schedules = []
            
            return render_template('faculty/profile.html', faculty=faculty, schedules=schedules)
            
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
            
            # Get room's schedule (if schedules table exists)
            schedules = []
            try:
                cursor.execute("""
                    SELECT sc.*, sec.section_name, sec.section_id,
                           f.name as faculty_name, f.faculty_id, sub.subject_name
                    FROM schedules sc
                    LEFT JOIN sections sec ON sc.section_id = sec.section_id
                    LEFT JOIN faculty f ON sc.faculty_id = f.faculty_id
                    LEFT JOIN subjects sub ON sc.subject_id = sub.subject_id
                    WHERE sc.room_id = %s
                    ORDER BY sc.day, sc.time
                """, (room_id,))
                schedules = cursor.fetchall()
            except:
                # If schedules table doesn't exist, use empty list
                schedules = []
            
            return render_template('room/profile.html', room=room, schedules=schedules)
            
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
            
            # Add students list to each section for compatibility
            for section in sections:
                section['students'] = []
            
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
            
            # Get section's schedule (if schedules table exists)
            schedules = []
            try:
                cursor.execute("""
                    SELECT sc.*, f.name as faculty_name, f.faculty_id,
                           r.room_name, r.room_id, sub.subject_name
                    FROM schedules sc
                    LEFT JOIN faculty f ON sc.faculty_id = f.faculty_id
                    LEFT JOIN rooms r ON sc.room_id = r.room_id
                    LEFT JOIN subjects sub ON sc.subject_id = sub.subject_id
                    WHERE sc.section_id = %s
                    ORDER BY sc.day, sc.time
                """, (section_id,))
                schedules = cursor.fetchall()
            except:
                # If schedules table doesn't exist, use empty list
                schedules = []
            
            return render_template('section/profile.html', section=section, students=students, schedules=schedules)
            
        except mysql.connector.Error as e:
            flash(f'Error loading section: {e}', 'error')
            return redirect(url_for('section_list'))
        finally:
            cursor.close()
            conn.close()

    @app.route('/pc-tracking')
    def pc_tracking():
        return render_template('pc_tracking.html')

    @app.route('/submit-documents')
    def submit_documents():
        return render_template('submit_documents.html')

    @app.route('/schedule')
    def schedule():
        return render_template('schedule.html')
    
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/contact')
    def contact():
        return render_template('contact.html')
    
    @app.route('/news')
    def news():
        return render_template('news.html')
    
    @app.route('/events')
    def events():
        return render_template('events.html')
    
    # ==================== TEST/DEBUG ROUTES ====================
    
    @app.route('/test-db')
    def test_db():
        conn = get_db_connection()
        if not conn:
            return "Database connection FAILED!"
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) as count FROM admin")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return f"Database connection SUCCESS! Admin count: {result['count']}"
        except Exception as e:
            return f"Database query FAILED: {e}"

    @app.route('/test-admin-data')
    def test_admin_data():
        """Test route to see admin data"""
        conn = get_db_connection()
        if not conn:
            return "Database connection FAILED!"
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT admin_id, username, password, full_name, email, role, is_active FROM admin")
            admins = cursor.fetchall()
            cursor.close()
            conn.close()
            
            html = "<h2>Admin Data in Database:</h2>"
            html += "<table border='1' style='border-collapse: collapse; padding: 10px;'>"
            html += "<tr><th>ID</th><th>Username</th><th>Password</th><th>Full Name</th><th>Email</th><th>Role</th><th>Active</th></tr>"
            
            for admin in admins:
                html += f"<tr>"
                html += f"<td>{admin.get('admin_id', 'N/A')}</td>"
                html += f"<td>{admin.get('username', 'N/A')}</td>"
                html += f"<td>{admin.get('password', 'N/A')}</td>"
                html += f"<td>{admin.get('full_name', 'N/A')}</td>"
                html += f"<td>{admin.get('email', 'N/A')}</td>"
                html += f"<td>{admin.get('role', 'N/A')}</td>"
                html += f"<td>{admin.get('is_active', 'N/A')}</td>"
                html += f"</tr>"
            
            html += "</table>"
            html += f"<br><p>Total admin records: {len(admins)}</p>"
            html += "<br><a href='/admin/login'>Try Admin Login</a>"
            
            return html
            
        except Exception as e:
            return f"Database query FAILED: {e}"
