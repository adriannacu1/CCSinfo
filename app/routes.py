from flask import render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from datetime import datetime, timedelta
import hashlib
import time
import random
import string
import traceback
import urllib.parse
from app import bcrypt

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
        # Get database statistics for the landing page
        conn = get_db_connection()
        stats = {
            'total_faculty': 0,
            'total_rooms': 0,
            'total_courses': 0
        }
        
        if conn:
            try:
                cursor = conn.cursor()
                
                # Count faculty
                cursor.execute("SELECT COUNT(*) FROM faculty")
                stats['total_faculty'] = cursor.fetchone()[0] or 0
                
                # Count rooms
                cursor.execute("SELECT COUNT(*) FROM rooms")
                stats['total_rooms'] = cursor.fetchone()[0] or 0
                
                # Count courses/programs
                cursor.execute("SELECT COUNT(*) FROM courses")
                stats['total_courses'] = cursor.fetchone()[0] or 0
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Error getting landing page stats: {e}")
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
        
        return render_template('index.html', stats=stats)

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
            'role': session.get('admin_role', 'admin')  # Make sure role is included
        }
        
        # Get database statistics
        conn = get_db_connection()
        stats = {
            'total_faculty': 0,
            'active_faculty': 0,
            'total_rooms': 0,
            'available_rooms': 0,
            'total_sections': 0,
            'active_sections': 0,
            'total_courses': 0,
            'total_temp_keys': 0
        }
        
        if conn:
            try:
                cursor = conn.cursor()
                
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
                
                # Count courses
                cursor.execute("SELECT COUNT(*) FROM courses")
                stats['total_courses'] = cursor.fetchone()[0] or 0
                
                # Count temporary keys
                cursor.execute("SELECT COUNT(*) FROM rand_strings")
                stats['total_temp_keys'] = cursor.fetchone()[0] or 0
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Error getting stats: {e}")
        
        recent_faculty = []
        
        return render_template('admin/dashboard.html', 
                         admin=admin_info,
                         stats=stats,
                         recent_faculty=recent_faculty)

    @app.route('/admin/faculty', methods=['GET', 'POST'])
    def admin_faculty():
        """Admin faculty management with CRUD operations"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin_info = {
            'admin_id': session.get('admin_id'),
            'username': session.get('admin_username'),
            'full_name': session.get('admin_name', 'Administrator'),
            'role': session.get('admin_role', 'admin')  # Make sure role is included
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
            'role': session.get('admin_role', 'admin')  # Make sure role is included
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
            'role': session.get('admin_role', 'admin')  # Make sure role is included
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
                
                # Get sections
                cursor.execute("""
                    SELECT s.*
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
            
            # Get schedules for this room
            cursor.execute("""
                SELECT s.*, 
                       sec.section_name,
                       s.subject,
                       f.name as faculty_name,
                       s.time
                FROM schedule s
                LEFT JOIN sections sec ON s.section_id = sec.section_id
                LEFT JOIN faculty f ON s.faculty_id = f.faculty_id
                WHERE s.room_id = %s
                ORDER BY FIELD(s.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
            """, (room_id,))
            schedules = cursor.fetchall()

            return render_template('admin/room_profile.html', 
                                room=room,
                                schedules=schedules)

        except Exception as e:
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
            
            # Get all sections with course info
            sections_query = """
            SELECT s.section_id, s.section_name, s.course, s.year_level
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
            
            return render_template('section/profile.html', section=section)
            
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
        """Admin settings page with profile management and system info"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))

        conn = get_db_connection()
        if not conn:
            flash('Database connection failed', 'error')
            return redirect(url_for('admin_dashboard'))

        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get current admin profile
            cursor.execute("""
                SELECT admin_id, username, full_name, email, role, 
                       last_login, created_at, login_attempts
                FROM admin 
                WHERE admin_id = %s
            """, (session['admin_id'],))
            admin_profile = cursor.fetchone()
            
            # Get system statistics
            stats = {}
            
            # Get total counts
            cursor.execute("SELECT COUNT(*) as count FROM students")
            stats['total_students'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM faculty")
            stats['total_faculty'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM rooms")
            stats['total_rooms'] = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM sections")
            stats['total_sections'] = cursor.fetchone()['count']
            
            # Count active temporary keys (generated in last 24 hours)
            cursor.execute("SELECT COUNT(*) as count FROM rand_strings WHERE Date > DATE_SUB(NOW(), INTERVAL 24 HOUR)")
            stats['active_temp_keys'] = cursor.fetchone()['count']
            
            # Get recent faculty activity (last 10 logins)
            cursor.execute("""
                SELECT f.name as faculty_name, f.last_login, f.department
                FROM faculty f
                WHERE f.last_login IS NOT NULL
                ORDER BY f.last_login DESC
                LIMIT 10
            """)
            recent_activity = cursor.fetchall()
            
            return render_template('admin/settings.html', 
                                 admin_profile=admin_profile,
                                 stats=stats,
                                 recent_activity=recent_activity)

        except mysql.connector.Error as e:
            flash(f'Database error: {str(e)}', 'error')
            return redirect(url_for('admin_dashboard'))
        finally:
            if conn:
                conn.close()

    @app.route('/admin/settings/update-profile', methods=['POST'])
    def admin_update_profile():
        """Update admin profile information"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))

        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()

        if not full_name or not email:
            flash('Full name and email are required', 'error')
            return redirect(url_for('admin_settings'))

        conn = get_db_connection()
        if not conn:
            flash('Database connection failed', 'error')
            return redirect(url_for('admin_settings'))

        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE admin 
                SET full_name = %s, email = %s, updated_at = NOW()
                WHERE admin_id = %s
            """, (full_name, email, session['admin_id']))
            
            flash('Profile updated successfully', 'success')

        except mysql.connector.Error as e:
            flash(f'Error updating profile: {str(e)}', 'error')
        finally:
            if conn:
                conn.close()

        return redirect(url_for('admin_settings'))

    @app.route('/admin/settings/change-password', methods=['POST'])
    def admin_change_password():
        """Change admin password"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))

        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([current_password, new_password, confirm_password]):
            flash('All password fields are required', 'error')
            return redirect(url_for('admin_settings'))

        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('admin_settings'))

        if len(new_password) < 6:
            flash('New password must be at least 6 characters long', 'error')
            return redirect(url_for('admin_settings'))

        conn = get_db_connection()
        if not conn:
            flash('Database connection failed', 'error')
            return redirect(url_for('admin_settings'))

        try:
            from app import bcrypt
            cursor = conn.cursor(dictionary=True)
            
            # Get current password hash
            cursor.execute("SELECT password FROM admin WHERE admin_id = %s", (session['admin_id'],))
            admin_data = cursor.fetchone()
            
            if not admin_data:
                flash('Admin not found', 'error')
                return redirect(url_for('admin_settings'))

            # Verify current password
            if not verify_admin_password(admin_data['password'], current_password):
                flash('Current password is incorrect', 'error')
                return redirect(url_for('admin_settings'))

            # Hash new password
            new_password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            
            # Update password
            cursor.execute("""
                UPDATE admin 
                SET password = %s, updated_at = NOW()
                WHERE admin_id = %s
            """, (new_password_hash, session['admin_id']))
            
            flash('Password changed successfully', 'success')

        except mysql.connector.Error as e:
            flash(f'Error changing password: {str(e)}', 'error')
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
        finally:
            if conn:
                conn.close()

        return redirect(url_for('admin_settings'))
    
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
                       s.subject,
                       r.room_name,
                       s.time
                FROM schedule s
                LEFT JOIN sections sec ON s.section_id = sec.section_id
                LEFT JOIN rooms r ON s.room_id = r.room_id
                WHERE s.faculty_id = %s
                ORDER BY FIELD(s.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')
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
        """View room profile with schedules"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))

        conn = get_db_connection()
        if not conn:
            flash('Database connection failed', 'error')
            return redirect(url_for('admin_rooms'))

        try:
            cursor = conn.cursor(dictionary=True)

            # Fetch room details
            cursor.execute("SELECT * FROM rooms WHERE room_id = %s", (room_id,))
            room = cursor.fetchone()

            if not room:
                flash('Room not found', 'error')
                return redirect(url_for('admin_rooms'))

            # Fix: Change 'schedules' to 'schedule' (singular)
            cursor.execute("""
                SELECT s.*, 
                       sec.section_name,
                       sub.subject_name as subject,
                       f.name as faculty_name,
                       s.time
                FROM schedule s
                LEFT JOIN sections sec ON s.section_id = sec.section_id
                LEFT JOIN subjects sub ON s.subject_id = sub.subject_id
                LEFT JOIN faculty f ON s.faculty_id = f.faculty_id
                WHERE s.room_id = %s
                ORDER BY FIELD(s.day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'),
                         s.time
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

            # Fetch section details
            cursor.execute("""
                SELECT s.*
                FROM sections s
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

            cursor.close()
            conn.close()

            return render_template('admin/section_profile.html',
                                section=section,
                                students=students)

        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return redirect(url_for('admin_sections'))

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
            
            # Test basic faculty query
            cursor.execute('SELECT COUNT(*) as count FROM faculty')
            faculty_count = cursor.fetchone()
            
            # Test getting a sample faculty
            cursor.execute('SELECT * FROM faculty LIMIT 1')
            sample_faculty = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True, 
                'faculty_count': faculty_count['count'],
                'sample_faculty': sample_faculty
            })
            
        except Exception as e:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500    @app.route('/admin/generate_temp_key', methods=['POST'])
    def admin_generate_temp_key():
        """Generate temporary access keys for room access"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        try:
            data = request.get_json()
            key_type = data.get('key_type')
            
            # Validate key type
            valid_types = ['5minutes', 'Mayoral', 'Maintenance']
            if key_type not in valid_types:
                return jsonify({'success': False, 'message': 'Invalid key type'}), 400
            
            # Generate random 7-digit code
            import random
            import string
            from datetime import datetime
            
            random_code = ''.join(random.choices(string.digits, k=7))
            current_time = datetime.now()
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor()
                
                # Insert the generated code into rand_strings table
                sql = "INSERT INTO rand_strings (randomC, Date, State) VALUES (%s, %s, %s)"
                cursor.execute(sql, (random_code, current_time, key_type))
                conn.commit()
                
                cursor.close()
                conn.close()
                
                # Map key types to display names
                key_display_names = {
                    '5minutes': '5-Minute Access',
                    'Mayoral': 'Mayoral Access', 
                    'Maintenance': 'Maintenance Access'
                }
                
                return jsonify({
                    'success': True, 
                    'message': f'{key_display_names[key_type]} code generated successfully',
                    'code': random_code,
                    'type': key_display_names[key_type],
                    'generated_at': current_time.strftime('%Y-%m-%d %H:%M:%S')
                })
                
            except Exception as e:
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
                return jsonify({'success': False, 'message': f'Database error: {str(e)}'}), 500
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    @app.route('/admin/get_temp_keys')
    def admin_get_temp_keys():
        """Get recent temporary keys generated by admin"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get recent keys from last 24 hours
            cursor.execute("""
                SELECT randomC, Date, State 
                FROM rand_strings 
                WHERE Date >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
                ORDER BY Date DESC 
                LIMIT 10
            """)
            
            keys = cursor.fetchall()
            
            # Format the keys for display
            formatted_keys = []
            for key in keys:
                key_display_names = {
                    '5minutes': '5-Minute Access',
                    'Mayoral': 'Mayoral Access', 
                    'Maintenance': 'Maintenance Access'
                }
                
                formatted_keys.append({
                    'code': key['randomC'],
                    'type': key_display_names.get(key['State'], key['State']),
                    'generated_at': key['Date'].strftime('%Y-%m-%d %H:%M:%S') if key['Date'] else 'Unknown',
                    'state': key['State']
                })
            
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'keys': formatted_keys})
            
        except Exception as e:
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

    @app.route('/admin/temp-keys')
    def admin_temp_keys():
        """Temporary keys management page"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        # Get admin info from session
        admin_info = {
            'admin_id': session.get('admin_id'),
            'username': session.get('admin_username'),
            'full_name': session.get('admin_name', 'Administrator'),
            'role': session.get('admin_role', 'admin')  # Make sure role is included
        }
        
        # Get recent generated keys for display
        conn = get_db_connection()
        recent_keys = []
        
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT randomC, Date, State, ID 
                    FROM rand_strings 
                    ORDER BY Date DESC 
                    LIMIT 10
                """)
                recent_keys = cursor.fetchall()
                cursor.close()
                conn.close()
            except Exception as e:
                print(f"Error fetching recent keys: {e}")
        
        return render_template('admin/temp_keys.html', admin=admin_info, recent_keys=recent_keys)

    
    @app.route('/api/admin/dashboard/stats')
    def api_dashboard_stats():
        """API endpoint for real-time dashboard statistics"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        conn = get_db_connection()
        stats = {
            'total_students': 0,
            'active_students': 0,
            'total_faculty': 0,
            'active_faculty': 0,
            'total_rooms': 0,
            'available_rooms': 0,
            'total_sections': 0,
            'active_sections': 0,
            'total_courses': 0,
            'total_temp_keys': 0
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
                
                # Count courses/programs
                cursor.execute("SELECT COUNT(*) FROM courses")
                stats['total_courses'] = cursor.fetchone()[0] or 0
                
                # Count temporary keys
                cursor.execute("SELECT COUNT(*) FROM rand_strings")
                stats['total_temp_keys'] = cursor.fetchone()[0] or 0
                
                cursor.close()
                conn.close()
                
                return jsonify({'success': True, 'stats': stats})
                
            except Exception as e:
                print(f"Error getting stats: {e}")
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
                return jsonify({'success': False, 'message': 'Database error'}), 500
        else:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500

    # Admin Management API Routes
    @app.route('/admin/get_admin/<int:admin_id>')
    def get_admin_api(admin_id):
        """API endpoint to get admin data"""
        if 'admin_id' not in session or session.get('admin_role') != 'super_admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                SELECT admin_id as id, username, full_name, email, role, 
                       is_active as status, last_login, created_at, login_attempts
                FROM admin WHERE admin_id = %s
            """, (admin_id,))
            admin = cursor.fetchone()
            
            if admin:
                return jsonify({'success': True, 'admin': admin})
            else:
                return jsonify({'success': False, 'message': 'Admin not found'}), 404
                
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if conn:
                conn.close()

    @app.route('/admin/add_admin', methods=['POST'])
    def add_admin_api():
        """API endpoint to add new admin"""
        if 'admin_id' not in session or session.get('admin_role') != 'super_admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        try:
            # Debug: print received form data
            print("DEBUG: Received form data:", dict(request.form))
            
            username = request.form.get('username')
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            role = request.form.get('role')
            password = request.form.get('password')
            notes = request.form.get('notes', '')
            
            print(f"DEBUG: Parsed values - username: '{username}', full_name: '{full_name}', email: '{email}', role: '{role}', password: '{password}'")
            
            if not all([username, full_name, email, role, password]):
                missing = []
                if not username: missing.append('username')
                if not full_name: missing.append('full_name')
                if not email: missing.append('email')
                if not role: missing.append('role')
                if not password: missing.append('password')
                print(f"DEBUG: Missing fields: {missing}")
                return jsonify({'success': False, 'message': f'All required fields must be filled. Missing: {", ".join(missing)}'}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor()
                
                # Check if username already exists
                cursor.execute("SELECT admin_id FROM admin WHERE username = %s", (username,))
                if cursor.fetchone():
                    return jsonify({'success': False, 'message': 'Username already exists'}), 400
                
                # Hash password
                password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
                
                # Insert new admin
                cursor.execute("""
                    INSERT INTO admin (username, full_name, email, role, password, is_active, created_at)
                    VALUES (%s, %s, %s, %s, %s, 1, NOW())
                """, (username, full_name, email, role, password_hash))
                
                conn.commit()
                return jsonify({'success': True, 'message': 'Admin added successfully'})
                
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/admin/update_admin/<int:admin_id>', methods=['PUT', 'POST'])
    def update_admin_api(admin_id):
        """API endpoint to update admin"""
        if 'admin_id' not in session or session.get('admin_role') != 'super_admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        try:
            username = request.form.get('username')
            full_name = request.form.get('full_name')
            email = request.form.get('email')
            role = request.form.get('role')
            notes = request.form.get('notes', '')
            password = request.form.get('password')
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor()
                
                # Check if username conflicts with other admins
                cursor.execute("SELECT admin_id FROM admin WHERE username = %s AND admin_id != %s", (username, admin_id))
                if cursor.fetchone():
                    return jsonify({'success': False, 'message': 'Username already exists'}), 400
                
                # Update admin (with or without password)
                if password:
                    from app import bcrypt
                    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
                    cursor.execute("""
                        UPDATE admin 
                        SET username = %s, full_name = %s, email = %s, role = %s, password = %s, updated_at = NOW()
                        WHERE admin_id = %s
                    """, (username, full_name, email, role, password_hash, admin_id))
                else:
                    cursor.execute("""
                        UPDATE admin 
                        SET username = %s, full_name = %s, email = %s, role = %s, updated_at = NOW()
                        WHERE admin_id = %s
                    """, (username, full_name, email, role, admin_id))
                
                conn.commit()
                return jsonify({'success': True, 'message': 'Admin updated successfully'})
                
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/admin/toggle_admin_status/<int:admin_id>', methods=['POST'])
    def toggle_admin_status_api(admin_id):
        """API endpoint to toggle admin status"""
        if 'admin_id' not in session or session.get('admin_role') != 'super_admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        # Prevent deactivating own account
        if admin_id == session.get('admin_id'):
            return jsonify({'success': False, 'message': 'Cannot deactivate your own account'}), 400
        
        try:
            data = request.get_json()
            new_status = 1 if data.get('status') == 'active' else 0
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor()
                cursor.execute("UPDATE admin SET is_active = %s WHERE admin_id = %s", (new_status, admin_id))
                conn.commit()
                
                status_text = 'activated' if new_status else 'deactivated'
                return jsonify({'success': True, 'message': f'Admin {status_text} successfully'})
                
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/admin/delete_admin/<int:admin_id>', methods=['DELETE'])
    def delete_admin_api(admin_id):
        """API endpoint to delete admin"""
        if 'admin_id' not in session or session.get('admin_role') != 'super_admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        # Prevent deleting own account
        if admin_id == session.get('admin_id'):
            return jsonify({'success': False, 'message': 'Cannot delete your own account'}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM admin WHERE admin_id = %s", (admin_id,))
            conn.commit()
            
            return jsonify({'success': True, 'message': 'Admin deleted successfully'})
            
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500
        finally:
            if conn:
                conn.close()

    @app.route('/admin/bulk_toggle_status', methods=['POST'])
    def bulk_toggle_admin_status():
        """API endpoint for bulk status toggle"""
        if 'admin_id' not in session or session.get('admin_role') != 'super_admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        try:
            data = request.get_json()
            admin_ids = data.get('admin_ids', [])
            
            # Remove current user from list
            current_admin_id = session.get('admin_id')
            admin_ids = [aid for aid in admin_ids if int(aid) != current_admin_id]
            
            if not admin_ids:
                return jsonify({'success': False, 'message': 'No valid admins selected'}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor()
                
                # Toggle status for each admin
                for admin_id in admin_ids:
                    cursor.execute("UPDATE admin SET is_active = NOT is_active WHERE admin_id = %s", (admin_id,))
                
                conn.commit()
                return jsonify({'success': True, 'message': f'{len(admin_ids)} admin(s) status updated'})
                
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/admin/bulk_delete_admins', methods=['DELETE'])
    def bulk_delete_admins():
        """API endpoint for bulk delete"""
        if 'admin_id' not in session or session.get('admin_role') != 'super_admin':
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        try:
            data = request.get_json()
            admin_ids = data.get('admin_ids', [])
            
            # Remove current user from list
            current_admin_id = session.get('admin_id')
            admin_ids = [aid for aid in admin_ids if int(aid) != current_admin_id]
            
            if not admin_ids:
                return jsonify({'success': False, 'message': 'No valid admins selected'}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor()
                
                # Delete admins
                for admin_id in admin_ids:
                    cursor.execute("DELETE FROM admin WHERE admin_id = %s", (admin_id,))
                
                conn.commit()
                return jsonify({'success': True, 'message': f'{len(admin_ids)} admin(s) deleted successfully'})
                
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)}), 500

    @app.route('/admin/events/add', methods=['POST'])
    def admin_add_event():
        """Add new event via admin panel"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        try:
            # Get form data
            event_name = request.form.get('event_title')
            description = request.form.get('description')
            category = request.form.get('category')
            event_date = request.form.get('event_date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            location = request.form.get('location')
            featured_image = request.form.get('featured_image_url')
            
            # Validate required fields
            if not all([event_name, description, category, event_date, start_time, location]):
                return jsonify({'success': False, 'message': 'All required fields must be filled'}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor()
                
                # Convert time strings to TIME format for MySQL
                start_time_formatted = datetime.strptime(start_time, '%H:%M').time()
                if end_time:
                    end_time_formatted = datetime.strptime(end_time, '%H:%M').time()
                else:
                    end_time_formatted = None
                
                # Insert new event - FIXED: using 'title' instead of 'event_name'
                cursor.execute("""
                    INSERT INTO events (title, description, category, event_date, event_time, end_time, 
                                       location, featured_image, status, created_by, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'upcoming', %s, NOW())
                """, (event_name, description, category, event_date, start_time_formatted, end_time_formatted,
                      location, featured_image, session.get('admin_id')))
                
                conn.commit()
                return jsonify({'success': True, 'message': 'Event created successfully'})
                
            except Exception as e:
                print(f"Error adding event: {e}")
                return jsonify({'success': False, 'message': f'Error creating event: {str(e)}'}), 500
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            print(f"Error in add_event: {e}")
            return jsonify({'success': False, 'message': f'Error creating event: {str(e)}'}), 500

    @app.route('/admin/events/update/<int:event_id>', methods=['POST'])
    def admin_update_event(event_id):
        """Update existing event via admin panel"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        try:
            # Get form data
            event_name = request.form.get('event_title')
            description = request.form.get('description')
            category = request.form.get('category')
            event_date = request.form.get('event_date')
            start_time = request.form.get('start_time')
            end_time = request.form.get('end_time')
            location = request.form.get('location')
            featured_image = request.form.get('featured_image_url')
            
            # Validate required fields
            if not all([event_name, description, category, event_date, start_time, location]):
                return jsonify({'success': False, 'message': 'All required fields must be filled'}), 400
            
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            
            try:
                cursor = conn.cursor()
                
                # Convert time strings to TIME format for MySQL
                start_time_formatted = datetime.strptime(start_time, '%H:%M').time()
                if end_time:
                    end_time_formatted = datetime.strptime(end_time, '%H:%M').time()
                else:
                    end_time_formatted = None
                
                # Update event - FIXED: using 'title' instead of 'event_name'
                cursor.execute("""
                    UPDATE events 
                    SET title = %s, description = %s, category = %s, event_date = %s, 
                        event_time = %s, end_time = %s, location = %s, 
                        featured_image = %s
                    WHERE event_id = %s
                """, (event_name, description, category, event_date, start_time_formatted, end_time_formatted,
                      location, featured_image, event_id))
                
                if cursor.rowcount == 0:
                    return jsonify({'success': False, 'message': 'Event not found'}), 404
                
                conn.commit()
                return jsonify({'success': True, 'message': 'Event updated successfully'})
                
            except Exception as e:
                print(f"Error updating event: {e}")
                return jsonify({'success': False, 'message': f'Error updating event: {str(e)}'}), 500
            finally:
                if conn:
                    conn.close()
                    
        except Exception as e:
            print(f"Error in update_event: {e}")
            return jsonify({'success': False, 'message': f'Error updating event: {str(e)}'}), 500

    @app.route('/admin/events/delete/<int:event_id>', methods=['DELETE', 'POST'])
    def admin_delete_event(event_id):
        """Delete event via admin panel"""
        if 'admin_id' not in session:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor()
            
            # Delete associated event speakers first
            cursor.execute("DELETE FROM event_speakers WHERE event_id = %s", (event_id,))
            
            # Delete the event
            cursor.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
            
            if cursor.rowcount == 0:
                return jsonify({'success': False, 'message': 'Event not found'}), 404
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Event deleted successfully'})
            
        except Exception as e:
            print(f"Error deleting event: {e}")
            return jsonify({'success': False, 'message': f'Error deleting event: {str(e)}'}), 500
        finally:
            if conn:
                conn.close()

    @app.route('/api/events/<int:event_id>')
    def get_event_details(event_id):
        """API endpoint to get detailed event information"""
        print(f"=== API request for event ID: {event_id} ===")
        
        conn = get_db_connection()
        
        if not conn:
            print("❌ Database connection failed")
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get event details first
            print(f"🔍 Querying event with ID: {event_id}")
            cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
            event = cursor.fetchone()
            
            if not event:
                print(f"❌ Event with ID {event_id} not found")
                cursor.close()
                conn.close()
                return jsonify({'success': False, 'message': f'Event with ID {event_id} not found'}), 404
            
            print(f"✅ Found event: {event['title']}")
            
            # Get speakers separately
            print(f"🔍 Querying speakers for event ID: {event_id}")
            cursor.execute("""
                SELECT name, role, bio, avatar 
                FROM event_speakers 
                WHERE event_id = %s
                ORDER BY speaker_id
            """, (event_id,))
            speakers_raw = cursor.fetchall()
            
            print(f"✅ Found {len(speakers_raw)} speakers")
            
            # Convert speakers to list of dictionaries
            speakers = []
            for speaker in speakers_raw:
                speakers.append({
                    'name': speaker['name'],
                    'role': speaker['role'],
                    'bio': speaker['bio'] if speaker['bio'] else None,
                    'avatar': speaker['avatar'] if speaker['avatar'] else None
                })
            
            event['speakers'] = speakers
            
            print(f"📋 Processing time formatting for event")
            
            # Format time fields
            if event.get('event_time'):
                if hasattr(event['event_time'], 'seconds'):
                    total_seconds = event['event_time'].seconds
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    event['event_time_formatted'] = f"{hours:02d}:{minutes:02d}"
                else:
                    # Handle string time format
                    try:
                        event['event_time_formatted'] = str(event['event_time'])
                    except:
                        event['event_time_formatted'] = "TBA"
            else:
                event['event_time_formatted'] = "TBA"
            
            if event.get('end_time'):
                if hasattr(event['end_time'], 'seconds'):
                    total_seconds = event['end_time'].seconds
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    event['end_time_formatted'] = f"{hours:02d}:{minutes:02d}"
                else:
                    # Handle string time format
                    try:
                        event['end_time_formatted'] = str(event['end_time'])
                    except:
                        event['end_time_formatted'] = None
            else:
                event['end_time_formatted'] = None
            
            # Format date
            if event.get('event_date'):
                try:
                    if hasattr(event['event_date'], 'strftime'):
                        event['event_date_formatted'] = event['event_date'].strftime('%B %d, %Y')
                    else:
                        event['event_date_formatted'] = str(event['event_date'])
                except:
                    event['event_date_formatted'] = str(event['event_date'])
            else:
                event['event_date_formatted'] = "Date TBA"
            
            cursor.close()
            conn.close()
            
            print(f"✅ Successfully processed event data for ID: {event_id}")
            return jsonify({'success': True, 'event': event})
            
        except Exception as e:
            print(f"❌ Error loading event details for ID {event_id}: {str(e)}")
            print(f"📋 Error traceback: {traceback.format_exc()}")
            if 'cursor' in locals():
                cursor.close()
            if 'conn' in locals():
                conn.close()
            return jsonify({'success': False, 'message': f'Error loading event details: {str(e)}'}), 500

    @app.route('/events')
    def events_page():
        """Events page showing upcoming events"""
        conn = get_db_connection()
        events = []
        event_counts = {}
        
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                
                # Get upcoming events
                cursor.execute("""
                    SELECT * FROM events e
                    WHERE e.event_date >= CURDATE() AND e.status = 'upcoming'
                    ORDER BY e.event_date ASC, e.event_time ASC
                """)
                events_raw = cursor.fetchall()
                print(f"Found {len(events_raw)} upcoming events")
                
                # Process events and get speakers for each
                for event in events_raw:
                    # Get speakers for this event
                    cursor.execute("""
                        SELECT name, role, bio, avatar 
                        FROM event_speakers 
                        WHERE event_id = %s
                        ORDER BY speaker_id
                    """, (event['event_id'],))
                    speakers_raw = cursor.fetchall()
                    
                    # Convert speakers to list of dictionaries
                    speakers = []
                    for speaker in speakers_raw:
                        speakers.append({
                            'name': speaker['name'],
                            'role': speaker['role'],
                            'bio': speaker['bio'] if speaker['bio'] else None,
                            'avatar': speaker['avatar'] if speaker['avatar'] else None
                        })
                    
                    event['speakers'] = speakers
                    # Convert timedelta to time string if needed
                    if event.get('event_time') and hasattr(event['event_time'], 'seconds'):
                        # Convert timedelta to time string
                        total_seconds = event['event_time'].seconds
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        event['event_time_formatted'] = f"{hours:02d}:{minutes:02d}"
                    elif event.get('event_time'):
                        event['event_time_formatted'] = str(event['event_time'])
                    else:
                        event['event_time_formatted'] = "TBA"
                    
                    if event.get('end_time') and hasattr(event['end_time'], 'seconds'):
                        # Convert timedelta to time string
                        total_seconds = event['end_time'].seconds
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        event['end_time_formatted'] = f"{hours:02d}:{minutes:02d}"
                    elif event.get('end_time'):
                        event['end_time_formatted'] = str(event['end_time'])
                    else:
                        event['end_time_formatted'] = None
                    
                    events.append(event)
                
                # Get event counts by category
                cursor.execute("""
                    SELECT category, COUNT(*) as count
                    FROM events
                    WHERE event_date >= CURDATE() AND status = 'upcoming'
                    GROUP BY category
                """)
                counts_raw = cursor.fetchall()
                event_counts = {row['category']: row['count'] for row in counts_raw}
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Error loading events: {str(e)}")
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
        
        return render_template('events.html', events=events, event_counts=event_counts)

    @app.route('/events/<int:event_id>')
    def event_profile(event_id):
        """Event profile page showing detailed event information"""
        conn = get_db_connection()
        event = None
        related_events = []
        prev_event = None
        next_event = None
        
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                
                # Get the specific event
                cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
                event_raw = cursor.fetchone()
                
                if event_raw:
                    # Get speakers for this event
                    cursor.execute("""
                        SELECT name, role, bio, avatar 
                        FROM event_speakers 
                        WHERE event_id = %s
                        ORDER BY speaker_id
                    """, (event_id,))
                    speakers_raw = cursor.fetchall()
                    
                    # Convert speakers to list of dictionaries
                    speakers = []
                    for speaker in speakers_raw:
                        speakers.append({
                            'name': speaker['name'],
                            'role': speaker['role'],
                            'bio': speaker['bio'] if speaker['bio'] else None,
                            'avatar': speaker['avatar'] if speaker['avatar'] else None
                        })
                    
                    event_raw['speakers'] = speakers
                    
                    # Format time fields
                    if event_raw.get('event_time') and hasattr(event_raw['event_time'], 'seconds'):
                        total_seconds = event_raw['event_time'].seconds
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        event_raw['event_time_formatted'] = f"{hours:02d}:{minutes:02d}"
                    elif event_raw.get('event_time'):
                        event_raw['event_time_formatted'] = str(event_raw['event_time'])
                    else:
                        event_raw['event_time_formatted'] = "TBA"
                    
                    if event_raw.get('end_time') and hasattr(event_raw['end_time'], 'seconds'):
                        total_seconds = event_raw['end_time'].seconds
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        event_raw['end_time_formatted'] = f"{hours:02d}:{minutes:02d}"
                    elif event_raw.get('end_time'):
                        event_raw['end_time_formatted'] = str(event_raw['end_time'])
                    else:
                        event_raw['end_time_formatted'] = None
                    
                    event = event_raw
                    
                    # Get related events (same category, excluding current event)
                    cursor.execute("""
                        SELECT event_id, title, event_date, category
                        FROM events 
                        WHERE category = %s AND event_id != %s AND status = 'upcoming'
                        ORDER BY event_date ASC 
                        LIMIT 3
                    """, (event['category'], event_id))
                    related_events = cursor.fetchall()
                    
                    # Get previous and next events (by date)
                    cursor.execute("""
                        SELECT event_id, title FROM events 
                        WHERE event_date < %s AND status = 'upcoming'
                        ORDER BY event_date DESC LIMIT 1
                    """, (event['event_date'],))
                    prev_event = cursor.fetchone()
                    
                    cursor.execute("""
                        SELECT event_id, title FROM events 
                        WHERE event_date > %s AND status = 'upcoming'
                        ORDER BY event_date ASC LIMIT 1
                    """, (event['event_date'],))
                    next_event = cursor.fetchone()
                
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Error loading event profile for ID {event_id}: {str(e)}")
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
        
        return render_template('event_profile.html', 
                             event=event, 
                             related_events=related_events,
                             prev_event=prev_event,
                             next_event=next_event)

    @app.route('/api/events/<int:event_id>/register', methods=['POST'])
    def register_for_event(event_id):
        """API endpoint to register for an event"""
        # This would handle event registration
        # For now, return a placeholder response
        return jsonify({
            'success': True, 
            'message': 'Registration functionality would be implemented here'
        })
    
    @app.route('/admin/management')
    def admin_management():
        """Admin management page for super admins"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        # Check if user is super admin
        if session.get('admin_role') != 'super_admin':
            flash('Access denied. Super admin privileges required.', 'error')
            return redirect(url_for('admin_dashboard'))
        
        admin_info = {
            'admin_id': session.get('admin_id'),
            'username': session.get('admin_username'),
            'full_name': session.get('admin_name', 'Administrator'),
            'role': session.get('admin_role', 'admin')
        }
        
        # Get all admins from database
        conn = get_db_connection()
        admins = []
        admin_stats = {
            'total_admins': 0,
            'active_admins': 0,
            'super_admins': 0,
            'recent_logins': 0
        }
        
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("""
                    SELECT admin_id, username, full_name, email, role, 
                           is_active, last_login, created_at, login_attempts
                    FROM admin 
                    ORDER BY created_at DESC
                """)
                admins = cursor.fetchall()
                
                # Calculate admin statistics
                admin_stats['total_admins'] = len(admins)
                admin_stats['active_admins'] = sum(1 for admin in admins if admin.get('is_active', 0))
                admin_stats['super_admins'] = sum(1 for admin in admins if admin.get('role') == 'super_admin')
                
                # Count recent logins (last 7 days)
                cursor.execute("""
                    SELECT COUNT(*) as recent_count
                    FROM admin 
                    WHERE last_login >= DATE_SUB(NOW(), INTERVAL 7 DAY)
                """)
                recent_result = cursor.fetchone()
                admin_stats['recent_logins'] = recent_result['recent_count'] if recent_result else 0
                
                cursor.close()
                conn.close()
            except Exception as e:
                flash(f'Error loading admins: {str(e)}', 'error')
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
        
        return render_template('admin/admin_management.html', 
                             admin=admin_info,
                             admins=admins,
                             admin_stats=admin_stats)
    
    @app.route('/admin/events')
    def admin_event_management():
        """Admin event management page"""
        if 'admin_id' not in session:
            return redirect(url_for('admin_login'))
        
        admin_info = {
            'admin_id': session.get('admin_id'),
            'username': session.get('admin_username'),
            'full_name': session.get('admin_name', 'Administrator'),
            'role': session.get('admin_role', 'admin')
        }
        
        # Get events from database
        conn = get_db_connection()
        events = []
        event_stats = {
            'total_events': 0,
            'upcoming_events': 0,
            'past_events': 0,
            'total_speakers': 0
        }
        
        if conn:
            try:
                cursor = conn.cursor(dictionary=True)
                
                # Use the correct column names based on your events table structure
                cursor.execute("""
                    SELECT event_id, 
                           title as event_name,
                           event_date, 
                           event_time,
                           end_time, 
                           location, 
                           description,
                           category,
                           status,
                           featured_image,
                           created_at
                FROM events 
                ORDER BY event_date DESC, event_time DESC
                """)
                events = cursor.fetchall()
                
                # Process events to handle timedelta objects
                for event in events:
                    # Convert timedelta to time string if needed
                    if event.get('event_time') and hasattr(event['event_time'], 'seconds'):
                        # Convert timedelta to time string
                        total_seconds = event['event_time'].seconds
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        event['event_time_formatted'] = f"{hours:02d}:{minutes:02d}"
                    elif event.get('event_time'):
                        event['event_time_formatted'] = str(event['event_time'])
                    else:
                        event['event_time_formatted'] = "TBA"
                    
                    if event.get('end_time') and hasattr(event['end_time'], 'seconds'):
                        # Convert timedelta to time string
                        total_seconds = event['end_time'].seconds
                        hours = total_seconds // 3600
                        minutes = (total_seconds % 3600) // 60
                        event['end_time_formatted'] = f"{hours:02d}:{minutes:02d}"
                    elif event.get('end_time'):
                        event['end_time_formatted'] = str(event['end_time'])
                    else:
                        event['end_time_formatted'] = None
                
                # Calculate event statistics
                event_stats['total_events'] = len(events)
                
                for event in events:
                    status = event.get('status', '').lower()
                    if status == 'upcoming':
                        event_stats['upcoming_events'] += 1
                    elif status in ['completed', 'past']:
                        event_stats['past_events'] += 1
                
                # Get total speakers count
                cursor.execute("SELECT COUNT(*) as speaker_count FROM event_speakers")
                speaker_result = cursor.fetchone()
                event_stats['total_speakers'] = speaker_result['speaker_count'] if speaker_result else 0
            
                cursor.close()
                conn.close()
            
            except Exception as e:
                flash(f'Error loading events: {str(e)}', 'error')
                if 'cursor' in locals():
                    cursor.close()
                if 'conn' in locals():
                    conn.close()
        
        return render_template('admin/event_management.html', 
                             admin=admin_info,
                             events=events,
                             event_stats=event_stats)