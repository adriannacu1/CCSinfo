"""
Analytics Setup Script for CCS Info System
This script initializes the analytics tables and populates them with sample data
"""

import mysql.connector
from datetime import datetime, timedelta
import random

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

def create_analytics_tables():
    """Create analytics tables"""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        print("Creating analytics tables...")
        
        # Page views table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS page_views (
                id INT AUTO_INCREMENT PRIMARY KEY,
                page_path VARCHAR(255) NOT NULL,
                user_ip VARCHAR(45),
                user_agent TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX(page_path),
                INDEX(timestamp)
            )
        """)
        print("✓ Created page_views table")
        
        # System logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                level ENUM('info', 'warning', 'error') DEFAULT 'info',
                category VARCHAR(50) NOT NULL,
                user_id INT,
                user_name VARCHAR(255),
                action VARCHAR(255) NOT NULL,
                details TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX(level),
                INDEX(category),
                INDEX(timestamp)
            )
        """)
        print("✓ Created system_logs table")
        
        conn.commit()
        print("✓ All analytics tables created successfully")
        return True
        
    except mysql.connector.Error as e:
        print(f"Error creating analytics tables: {e}")
        return False
    finally:
        if conn:
            conn.close()

def populate_sample_data():
    """Populate analytics tables with sample data"""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        print("Populating sample analytics data...")
        
        # Clear existing data
        cursor.execute("DELETE FROM page_views")
        cursor.execute("DELETE FROM system_logs")
        
        # Sample page paths
        pages = ['/', '/admin/dashboard', '/admin/students', '/admin/faculty', 
                '/admin/rooms', '/admin/sections', '/admin/settings', '/admin/analytics']
        
        # Generate sample page views for the last 30 days
        print("Generating page views data...")
        for day in range(30):
            date = datetime.now() - timedelta(days=day)
            
            # Generate more views for recent days
            views_multiplier = max(0.5, 1 - (day * 0.02))
            
            for page in pages:
                # Different pages have different popularity
                if page == '/':
                    base_views = random.randint(15, 35)
                elif page == '/admin/dashboard':
                    base_views = random.randint(10, 25)
                else:
                    base_views = random.randint(3, 15)
                
                daily_views = int(base_views * views_multiplier)
                
                for _ in range(daily_views):
                    # Random time within the day
                    random_time = date.replace(
                        hour=random.randint(6, 22),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59)
                    )
                    
                    cursor.execute("""
                        INSERT INTO page_views (page_path, user_ip, user_agent, timestamp) 
                        VALUES (%s, %s, %s, %s)
                    """, (page, f"192.168.1.{random.randint(1, 254)}", 
                         "Mozilla/5.0 (Analytics Sample Data)", random_time))
        
        print("✓ Generated page views data")
        
        # Generate sample system logs
        print("Generating system logs data...")
        levels = ['info', 'warning', 'error']
        categories = ['auth', 'room', 'admin', 'system']
        actions = [
            'User login successful',
            'Room access granted',
            'Data updated',
            'System backup completed',
            'Password changed',
            'Invalid login attempt',
            'Room access denied',
            'System maintenance',
            'Database optimization',
            'User session expired'
        ]
        
        users = [
            'John Doe', 'Jane Smith', 'Mike Johnson', 'Sarah Wilson', 
            'David Brown', 'Admin', 'System', 'root'
        ]
        
        for day in range(30):
            date = datetime.now() - timedelta(days=day)
            
            # Generate 5-15 log entries per day
            daily_logs = random.randint(5, 15)
            
            for _ in range(daily_logs):
                random_time = date.replace(
                    hour=random.randint(0, 23),
                    minute=random.randint(0, 59),
                    second=random.randint(0, 59)
                )
                
                level = random.choice(levels)
                # More info logs, fewer errors
                if random.random() < 0.7:
                    level = 'info'
                elif random.random() < 0.9:
                    level = 'warning'
                else:
                    level = 'error'
                
                cursor.execute("""
                    INSERT INTO system_logs 
                    (level, category, user_name, action, details, timestamp) 
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    level,
                    random.choice(categories),
                    random.choice(users),
                    random.choice(actions),
                    f"System operation completed with {level} level",
                    random_time
                ))
        
        print("✓ Generated system logs data")
        
        conn.commit()
        print("✓ All sample data populated successfully")
        return True
        
    except mysql.connector.Error as e:
        print(f"Error populating sample data: {e}")
        return False
    finally:
        if conn:
            conn.close()

def main():
    """Main setup function"""
    print("=== CCS Info Analytics Setup ===")
    print("This script will set up analytics tables and populate sample data")
    print()
    
    # Create tables
    if create_analytics_tables():
        print()
        
        # Ask user if they want sample data
        response = input("Do you want to populate sample analytics data? (y/N): ").lower().strip()
        
        if response in ['y', 'yes']:
            if populate_sample_data():
                print()
                print("✅ Analytics setup completed successfully!")
                print()
                print("You can now:")
                print("1. Access the analytics dashboard at /admin/analytics")
                print("2. View detailed reports and charts")
                print("3. Export analytics data")
                print("4. Monitor system logs and user activity")
            else:
                print("❌ Failed to populate sample data")
        else:
            print("✅ Analytics tables created successfully!")
            print("You can now start collecting analytics data")
    else:
        print("❌ Failed to create analytics tables")

if __name__ == "__main__":
    main()
