import pymysql
import os

def create_database_from_sql():
    # Connect to MySQL server
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password=''
    )
    
    try:
        with conn.cursor() as cursor:
            # Create database if it doesn't exist
            cursor.execute('CREATE DATABASE IF NOT EXISTS ccs_info')
            cursor.execute('USE ccs_info')
            
            # Read SQL file content
            sql_file_path = os.path.join(os.path.dirname(__file__), 'pc_tracking_system.sql')
            with open(sql_file_path, 'r') as file:
                sql_content = file.read()
                
            # Split SQL statements and execute each one
            for statement in sql_content.split(';'):
                if statement.strip():
                    cursor.execute(statement)
                    
            conn.commit()
            print("Database created successfully from SQL file!")
    except Exception as e:
        print(f"Error creating database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_database_from_sql()