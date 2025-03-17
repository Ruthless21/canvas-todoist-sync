#!/usr/bin/env python3
"""
Comprehensive MySQL and Application Fixer for PythonAnywhere
This script diagnoses and fixes common issues with Flask applications on PythonAnywhere
"""
import os
import sys
import time
import socket
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants - update these with your actual credentials
USERNAME = 'TatumParr'
PASSWORD = 'v7rvtPEfz9iT'  # Your MySQL password
DB_NAME = 'TatumParr$canvas_todoist'
HOST = 'TatumParr.mysql.pythonanywhere-services.com'

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f" {text} ".center(70, '='))
    print("=" * 70)

def print_section(text):
    """Print a section header"""
    print("\n" + "-" * 60)
    print(f" {text} ".center(60, '-'))
    print("-" * 60)

def setup_environment():
    """Set up the environment like the WSGI file does"""
    # Patch socket.gethostname for PythonAnywhere
    socket.gethostname = lambda: 'pythonanywhere.com'
    
    # Set environment variables
    os.environ['FLASK_ENV'] = 'pythonanywhere'
    os.environ['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key-for-development')
    
    # Set database URL
    os.environ['DATABASE_URL'] = f"mysql+mysqldb://{USERNAME}:{PASSWORD}@{HOST}/{DB_NAME}"
    print(f"Environment set up with DATABASE_URL (password hidden for security)")

def test_direct_connection():
    """Test a direct connection to MySQL"""
    print_section("Testing Direct MySQL Connection")
    try:
        import MySQLdb
        print("✓ MySQLdb is installed correctly")

        print(f"Attempting to connect to MySQL database: {DB_NAME} on {HOST}")
        conn = MySQLdb.connect(
            user=USERNAME,
            passwd=PASSWORD,
            host=HOST,
            db=DB_NAME
        )
        print("✅ Direct connection successful!")
        
        # Show process list
        cursor = conn.cursor()
        cursor.execute("SHOW PROCESSLIST")
        processes = cursor.fetchall()
        
        print(f"\nFound {len(processes)} active MySQL processes:")
        print(f"{'ID':<8} {'User':<15} {'Host':<25} {'DB':<20} {'Command':<10} {'Time':<8} {'State':<15}")
        print("-" * 95)
        
        for process in processes:
            pid, user, host, db, command, time, state, info = process + (None,) * (8 - len(process))
            print(f"{pid:<8} {user:<15} {(host or '')[:25]:<25} {(db or 'None')[:20]:<20} {command:<10} {time:<8} {(state or 'None')[:15]:<15}")
        
        # Check for stale connections
        stale_connections = [p for p in processes if p[4] == 'Sleep' and p[5] > 240]
        if stale_connections:
            print(f"\n⚠️ Found {len(stale_connections)} stale connections (sleeping > 240 seconds)")
            kill_stale = input("Do you want to kill these stale connections? (y/n): ").lower() == 'y'
            
            if kill_stale:
                for process in stale_connections:
                    pid = process[0]
                    cursor.execute(f"KILL {pid}")
                    print(f"Killed connection {pid}")
                
                print("✅ Stale connections killed")
        
        cursor.close()
        conn.close()
        return True
    except ImportError as e:
        print(f"❌ MySQLdb not installed correctly: {str(e)}")
        print("Try running: pip install --user mysqlclient")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        traceback.print_exc()
        return False

def check_table_access():
    """Check if we can access tables in the database"""
    print_section("Testing Table Access")
    try:
        import MySQLdb
        conn = MySQLdb.connect(
            user=USERNAME,
            passwd=PASSWORD,
            host=HOST,
            db=DB_NAME
        )
        cursor = conn.cursor()
        
        # Show tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if tables:
            print(f"✅ Found {len(tables)} tables in the database:")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Check if we can query the user table
            if any('user' in t[0].lower() for t in tables):
                try:
                    cursor.execute("SELECT COUNT(*) FROM user")
                    count = cursor.fetchone()[0]
                    print(f"✅ Successfully queried user table: {count} users found")
                except Exception as e:
                    print(f"❌ Could not query user table: {str(e)}")
        else:
            print("⚠️ No tables found in the database. The database might be empty.")
            # Try to create a test table
            try:
                cursor.execute("CREATE TABLE _test_table (id INT, value VARCHAR(50))")
                cursor.execute("INSERT INTO _test_table VALUES (1, 'Test successful')")
                cursor.execute("SELECT * FROM _test_table")
                print(f"✅ Test table created and queried successfully: {cursor.fetchone()}")
                cursor.execute("DROP TABLE _test_table")
                print("✅ Test table dropped")
            except Exception as e:
                print(f"❌ Could not create test table: {str(e)}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Table access check failed: {str(e)}")
        return False

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection"""
    print_section("Testing SQLAlchemy Connection")
    try:
        from sqlalchemy import create_engine, text
        print("✓ SQLAlchemy is installed correctly")
        
        # Create engine with proper pooling settings
        url = f"mysql+mysqldb://{USERNAME}:{PASSWORD}@{HOST}/{DB_NAME}"
        print(f"Creating engine with connection URL: mysql+mysqldb://{USERNAME}:****@{HOST}/{DB_NAME}")
        
        engine = create_engine(
            url,
            pool_recycle=240,  # Less than PythonAnywhere's 300s timeout
            pool_pre_ping=True,
            pool_timeout=30,
            pool_size=5,
            max_overflow=2
        )
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"✅ Query executed successfully. Result: {result.scalar()}")
        
        print("✅ SQLAlchemy connection successful!")
        
        # Test connection pool
        print("Testing connection pool with 3 consecutive connections...")
        for i in range(3):
            with engine.connect() as connection:
                result = connection.execute(text(f"SELECT {i+1}"))
                print(f"  Connection {i+1}: query returned {result.scalar()}")
        
        # Cleanup
        engine.dispose()
        print("✓ Engine disposed, connections closed")
        return True
    except ImportError as e:
        print(f"❌ SQLAlchemy dependency issue: {str(e)}")
        print("Try running: pip install --user sqlalchemy mysqlclient")
        return False
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {str(e)}")
        traceback.print_exc()
        return False

def check_flask_app():
    """Test the Flask application configuration and connectivity"""
    print_section("Testing Flask Application")
    try:
        from app import create_app
        from models import db, User
        
        print("✓ Successfully imported Flask app modules")
        
        # Create app with PythonAnywhere config
        print("Creating Flask app with 'pythonanywhere' config...")
        app = create_app('pythonanywhere')
        
        print("Flask application configuration:")
        print(f"  SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        print(f"  SQLALCHEMY_ENGINE_OPTIONS: {app.config.get('SQLALCHEMY_ENGINE_OPTIONS')}")
        
        # Test database connection through Flask app
        print("Testing database access through Flask-SQLAlchemy...")
        with app.app_context():
            try:
                # Get user count
                user_count = User.query.count()
                print(f"✅ Database query successful: {user_count} users found")
                
                # Try to add a dummy user if none exist
                if user_count == 0:
                    try:
                        print("No users found. Attempting to create a test user...")
                        from werkzeug.security import generate_password_hash
                        test_user = User(
                            username="test_user",
                            email="test@example.com"
                        )
                        test_user.password_hash = generate_password_hash("password")
                        db.session.add(test_user)
                        db.session.commit()
                        print("✅ Test user created successfully")
                        
                        # Clean up
                        db.session.delete(test_user)
                        db.session.commit()
                        print("✅ Test user removed")
                    except Exception as e:
                        print(f"❌ Could not create test user: {str(e)}")
                        db.session.rollback()
                
                # Force cleanup
                db.session.remove()
                db.engine.dispose()
                print("✓ Database connections cleaned up")
            except Exception as e:
                print(f"❌ Flask-SQLAlchemy query failed: {str(e)}")
                traceback.print_exc()
                return False
        
        return True
    except ImportError as e:
        print(f"❌ Flask app import error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Flask app initialization failed: {str(e)}")
        traceback.print_exc()
        return False

def check_dependencies():
    """Check if all required packages are installed"""
    print_section("Checking Dependencies")
    
    required_packages = [
        'flask', 'flask_sqlalchemy', 'flask_login', 'sqlalchemy', 
        'mysqlclient', 'pymysql', 'python-dotenv'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            module_name = package.replace('-', '_')
            __import__(module_name)
            print(f"✓ {package} is installed")
        except ImportError:
            print(f"❌ {package} is NOT installed")
            all_installed = False
    
    if not all_installed:
        print("\n⚠️ Some required packages are missing. Run:")
        print("pip install --user -r requirements.txt")
    
    return all_installed

def main():
    """Main function to diagnose and fix issues"""
    print_header("PythonAnywhere MySQL and Flask Application Fixer")
    print("This script will diagnose and fix common issues with Flask applications")
    print("on PythonAnywhere, focusing on MySQL connection problems.")
    
    print(f"\nUsing MySQL credentials:")
    print(f"  Username: {USERNAME}")
    print(f"  Database: {DB_NAME}")
    print(f"  Host: {HOST}")
    
    # Set up environment like WSGI file
    setup_environment()
    
    # Check dependencies first
    deps_ok = check_dependencies()
    
    # Run all tests
    direct_ok = test_direct_connection()
    tables_ok = check_table_access() if direct_ok else False
    sqlalchemy_ok = test_sqlalchemy_connection()
    flask_ok = check_flask_app()
    
    # Print summary
    print_header("Test Results Summary")
    print(f"Dependencies check: {'✅ PASSED' if deps_ok else '❌ FAILED'}")
    print(f"Direct MySQL connection: {'✅ PASSED' if direct_ok else '❌ FAILED'}")
    print(f"Database tables access: {'✅ PASSED' if tables_ok else '❌ FAILED'}")
    print(f"SQLAlchemy connection: {'✅ PASSED' if sqlalchemy_ok else '❌ FAILED'}")
    print(f"Flask application: {'✅ PASSED' if flask_ok else '❌ FAILED'}")
    
    # Give recommendations
    print_header("Recommendations")
    
    if not deps_ok:
        print("1. Install missing dependencies:")
        print("   pip install --user -r requirements.txt")
    
    if not direct_ok:
        print("1. Check your MySQL password on PythonAnywhere Databases tab")
        print("2. Verify that database TatumParr$canvas_todoist exists")
        print("3. Check MySQL logs for any error messages")
    
    if direct_ok and not sqlalchemy_ok:
        print("1. Check SQLAlchemy connection string format")
        print("2. Ensure mysqlclient is properly installed")
    
    if not flask_ok and (direct_ok or sqlalchemy_ok):
        print("1. Check Flask application configuration")
        print("2. Check for errors in your models.py file")
    
    if all([direct_ok, sqlalchemy_ok, flask_ok]):
        print("All tests passed! Your database connection appears to be working correctly.")
        print("If you're still experiencing issues, try reloading your web app.")
    
    print("\nOnce fixes are applied, reload your web app from the PythonAnywhere dashboard.")
    print("Then check the error logs for any remaining issues.")

if __name__ == "__main__":
    main() 