#!/usr/bin/env python3
"""
MySQL Connection Fixer for PythonAnywhere
This script helps diagnose and fix MySQL connection issues in PythonAnywhere
"""
import os
import sys
import time
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants - update these with your actual credentials
USERNAME = 'TatumParr'
PASSWORD = 'FEo3f5gBOpIZF'  # Your MySQL password
DB_NAME = 'TatumParr$canvas_todoist'
HOST = 'TatumParr.mysql.pythonanywhere-services.com'

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def test_direct_connection():
    """Test a direct connection to MySQL"""
    print("Testing direct connection to MySQL...")
    try:
        import MySQLdb
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
        print(f"{'ID':<10} {'User':<15} {'Host':<25} {'DB':<20} {'Command':<10} {'Time':<10} {'State':<15}")
        print("-" * 100)
        
        for process in processes:
            pid, user, host, db, command, time, state, info = process + (None,) * (8 - len(process))
            print(f"{pid:<10} {user:<15} {host:<25} {db or 'None':<20} {command:<10} {time:<10} {state or 'None':<15}")
        
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
    except ImportError:
        print("❌ MySQLdb not installed. Try running:")
        print("pip install --user mysqlclient")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        traceback.print_exc()
        return False

def clear_environment():
    """Clear any existing DATABASE_URL environment variables"""
    if 'DATABASE_URL' in os.environ:
        del os.environ['DATABASE_URL']
        print("Cleared existing DATABASE_URL environment variable")

def set_database_url():
    """Set the proper DATABASE_URL environment variable"""
    url = f"mysql+mysqldb://{USERNAME}:{PASSWORD}@{HOST}/{DB_NAME}"
    os.environ['DATABASE_URL'] = url
    print(f"Set DATABASE_URL: mysql+mysqldb://{USERNAME}:****@{HOST}/{DB_NAME}")
    return url

def test_sqlalchemy():
    """Test SQLAlchemy connection"""
    print("\nTesting SQLAlchemy connection...")
    try:
        from sqlalchemy import create_engine, text
        url = set_database_url()
        
        engine = create_engine(
            url,
            pool_recycle=240,
            pool_pre_ping=True,
            pool_timeout=30,
            pool_size=5,
            max_overflow=2
        )
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            print(f"✅ SQLAlchemy connection successful! Result: {result}")
        
        engine.dispose()
        return True
    except ImportError:
        print("❌ SQLAlchemy not installed. Try running:")
        print("pip install --user sqlalchemy")
        return False
    except Exception as e:
        print(f"❌ SQLAlchemy connection failed: {str(e)}")
        traceback.print_exc()
        return False

def check_flask_config():
    """Check Flask application configuration"""
    print("\nChecking Flask application configuration...")
    try:
        from app import create_app
        app = create_app('pythonanywhere')
        
        print("Flask application configuration:")
        print(f"  SQLALCHEMY_DATABASE_URI = {app.config.get('SQLALCHEMY_DATABASE_URI')}")
        print(f"  SQLALCHEMY_ENGINE_OPTIONS = {app.config.get('SQLALCHEMY_ENGINE_OPTIONS')}")
        return True
    except ImportError:
        print("❌ Flask app modules not found")
        return False
    except Exception as e:
        print(f"❌ Error checking Flask configuration: {str(e)}")
        traceback.print_exc()
        return False

def fix_permissions():
    """Attempt to fix MySQL permissions"""
    print("\nAttempting to fix MySQL permissions...")
    try:
        import MySQLdb
        conn = MySQLdb.connect(
            user=USERNAME,
            passwd=PASSWORD,
            host=HOST,
            db=DB_NAME
        )
        cursor = conn.cursor()
        
        # Try to create a test table (will help identify permission issues)
        try:
            cursor.execute("CREATE TABLE IF NOT EXISTS __test_permissions (id INT PRIMARY KEY, test_value VARCHAR(50))")
            cursor.execute("INSERT INTO __test_permissions VALUES (1, 'Test successful')")
            cursor.execute("SELECT * FROM __test_permissions")
            print(f"✅ Permission test successful: {cursor.fetchone()}")
            cursor.execute("DROP TABLE __test_permissions")
        except Exception as e:
            print(f"⚠️ Permission test failed: {str(e)}")
        
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"❌ Cannot fix permissions: {str(e)}")
        traceback.print_exc()

def main():
    """Main function"""
    print_header("MySQL Connection Fixer for PythonAnywhere")
    print(f"Using MySQL credentials:")
    print(f"  Username: {USERNAME}")
    print(f"  Password: {'*' * len(PASSWORD)}")
    print(f"  Database: {DB_NAME}")
    print(f"  Host: {HOST}")
    
    # Clear environment
    clear_environment()
    
    # Test and fix connections
    direct_success = test_direct_connection()
    sqlalchemy_success = test_sqlalchemy()
    flask_config_success = check_flask_config()
    
    if not direct_success:
        print("\n⚠️ Direct MySQL connection failed. This suggests a credentials issue.")
        print("Check your MySQL password on PythonAnywhere Databases tab.")
    
    if not sqlalchemy_success and direct_success:
        print("\n⚠️ SQLAlchemy connection failed but direct connection worked.")
        print("This suggests an issue with the connection string format or SQLAlchemy configuration.")
    
    if not flask_config_success:
        print("\n⚠️ Flask app configuration check failed.")
        print("This suggests an issue with your Flask app configuration.")
    
    # Try to fix permissions if direct connection worked but other methods failed
    if direct_success and (not sqlalchemy_success or not flask_config_success):
        fix_permissions()
    
    print_header("Recommendations")
    
    if not direct_success:
        print("1. Verify your MySQL password on PythonAnywhere Databases tab")
        print("2. Check that your database (TatumParr$canvas_todoist) exists")
        print("3. Try restarting your MySQL database from PythonAnywhere dashboard")
    elif not sqlalchemy_success:
        print("1. Check your SQLAlchemy connection string format")
        print("2. Ensure mysqlclient is properly installed: pip install --user mysqlclient")
        print("3. Try reloading your web app")
    else:
        print("Your MySQL connection settings look good! Try reloading your web app.")
    
    print("\nRemember to check your web app error logs after reloading.")

if __name__ == "__main__":
    main() 