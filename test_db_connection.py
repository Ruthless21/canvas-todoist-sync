#!/usr/bin/env python3
"""
Database connection test script for PythonAnywhere
Run this script on PythonAnywhere to verify your database connection
"""
import os
import sys
import time
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project directory to sys.path if needed
project_folder = os.path.dirname(os.path.abspath(__file__))
if project_folder not in sys.path:
    sys.path.insert(0, project_folder)

def test_direct_mysqldb_connection():
    """Test direct connection to MySQL using MySQLdb"""
    try:
        import MySQLdb
        print("MySQLdb is installed correctly")

        # Get connection details from environment variables
        db_username = 'TatumParr'  # Your PythonAnywhere username
        db_password = 'FEo3f5gBOpIZF'  # Your MySQL password
        db_name = 'TatumParr$canvas_todoist'  # Format must be username$dbname
        db_host = 'TatumParr.mysql.pythonanywhere-services.com'  # Standard host format

        print(f"Connecting to MySQL database: {db_name} on {db_host}")
        conn = MySQLdb.connect(
            user=db_username,
            passwd=db_password,
            host=db_host,
            db=db_name
        )
        print("✅ Direct MySQLdb connection successful!")
        
        # Execute a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"Query result: {result}")
        
        cursor.close()
        conn.close()
        print("Connection closed properly")
        
        return True
    except ImportError as e:
        print(f"❌ Error: MySQLdb not installed correctly: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        traceback.print_exc()
        return False

def test_sqlalchemy_connection():
    """Test connection using SQLAlchemy"""
    try:
        from sqlalchemy import create_engine, text
        print("SQLAlchemy is installed correctly")
        
        # Get connection details from environment variables
        db_username = 'TatumParr'  # Your PythonAnywhere username
        db_password = 'FEo3f5gBOpIZF'  # Your MySQL password
        db_name = 'TatumParr$canvas_todoist'  # Format must be username$dbname
        db_host = 'TatumParr.mysql.pythonanywhere-services.com'  # Standard host format
        
        # Create the connection URL
        db_url = f"mysql+mysqldb://{db_username}:{db_password}@{db_host}/{db_name}"
        print(f"Connecting to SQLAlchemy engine with URL: {db_url.replace(db_password, '********')}")
        
        # Create engine with proper connection pooling settings
        engine = create_engine(
            db_url,
            pool_recycle=240,  # Less than PythonAnywhere's 300s timeout
            pool_pre_ping=True,
            pool_timeout=30,
            pool_size=5,
            max_overflow=2
        )
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print(f"Query result: {result.scalar()}")
            
        print("✅ SQLAlchemy connection successful!")
        
        # Test connection pool with multiple connections
        print("Testing connection pooling with 3 consecutive connections...")
        for i in range(3):
            with engine.connect() as connection:
                result = connection.execute(text(f"SELECT {i+1}"))
                print(f"  Connection {i+1} result: {result.scalar()}")
                time.sleep(1)  # Brief pause between connections
        
        # Test connection recycling
        print("Testing connection recycling after idle period...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 'Before idle'"))
            print(f"  Before idle: {result.scalar()}")
            
        print("  Waiting 3 seconds...")
        time.sleep(3)  # Simulate idle time (but less than pool_recycle)
        
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 'After idle'"))
            print(f"  After idle: {result.scalar()}")
        
        # Dispose of engine to close all connections
        engine.dispose()
        print("Engine disposed, all connections closed")
        
        return True
    except ImportError as e:
        print(f"❌ Error: SQLAlchemy not installed correctly: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ SQLAlchemy connection error: {str(e)}")
        traceback.print_exc()
        return False

def test_flask_app_connection():
    """Test Flask app's database connection"""
    try:
        print("Testing Flask application database connection...")
        from app import create_app
        from models import db, User
        
        # Create app with PythonAnywhere config
        app = create_app('pythonanywhere')
        
        with app.app_context():
            # Test connection by querying user count
            user_count = User.query.count()
            print(f"✅ Flask app database connection successful! User count: {user_count}")
            
            # Force cleanup
            db.session.remove()
            db.engine.dispose()
            print("Database connections cleaned up")
        
        return True
    except ImportError as e:
        print(f"❌ Error: Flask app modules not found: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Flask app database connection error: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("DATABASE CONNECTION TEST SCRIPT FOR PYTHONANYWHERE")
    print("=" * 60)
    print("This script will test your database connections in three ways:")
    print("1. Direct connection with MySQLdb")
    print("2. Connection with SQLAlchemy")
    print("3. Connection through your Flask application")
    print("=" * 60)
    
    # Run tests
    direct_success = test_direct_mysqldb_connection()
    print("\n" + "-" * 40 + "\n")
    
    sqlalchemy_success = test_sqlalchemy_connection()
    print("\n" + "-" * 40 + "\n")
    
    flask_success = test_flask_app_connection()
    print("\n" + "=" * 60)
    
    # Summary
    print("TEST RESULTS SUMMARY:")
    print(f"Direct MySQLdb Connection: {'✅ PASSED' if direct_success else '❌ FAILED'}")
    print(f"SQLAlchemy Connection: {'✅ PASSED' if sqlalchemy_success else '❌ FAILED'}")
    print(f"Flask App Connection: {'✅ PASSED' if flask_success else '❌ FAILED'}")
    
    if direct_success and sqlalchemy_success and flask_success:
        print("\n✅ ALL TESTS PASSED! Your database configuration appears to be working correctly.")
    else:
        print("\n❌ SOME TESTS FAILED. Review the errors above to fix your configuration.") 