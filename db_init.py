from app import app, db
from app.models import Admin
import hashlib
import pymysql

def initialize_database():
    # First, create the database if it doesn't exist
    try:
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password=''
        )
        with conn.cursor() as cursor:
            cursor.execute('CREATE DATABASE IF NOT EXISTS ccs_info')
        conn.close()
        print("Database 'ccs_info' created or already exists!")
    except Exception as e:
        print(f"Error creating database: {e}")
        return

    # Now create tables and admin user
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if admin user exists
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            # Create default admin (password: 123)
            admin = Admin(
                username='admin',
                password=hashlib.md5('123'.encode()).hexdigest(),
                full_name='Default Admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created!")
        
        print("Database initialized successfully!")

if __name__ == "__main__":
    initialize_database()