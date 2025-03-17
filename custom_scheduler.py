#!/usr/bin/env python3
"""
Custom scheduler script for PythonAnywhere scheduled tasks
This script runs sync operations directly without using Flask-APScheduler
"""
import os
import sys
from dotenv import load_dotenv
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('custom_scheduler')

# Load environment variables
project_folder = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(project_folder, '.env'))

# Add the project directory to sys.path if needed
if project_folder not in sys.path:
    sys.path.insert(0, project_folder)

def main():
    """Run sync for all enabled users"""
    try:
        # Import here to avoid circular imports
        from app import create_app
        from models import db, User, SyncSettings, SyncHistory
        from services.canvas_api import CanvasAPI
        from services.todoist_api import TodoistClient
        from services.sync_service import SyncService
        
        # Create app with production context
        app = create_app('production')
        
        with app.app_context():
            try:
                now = datetime.utcnow()
                logger.info(f"Starting scheduled sync at {now}")
                
                # Get all enabled sync settings
                settings = SyncSettings.query.filter_by(enabled=True).all()
                logger.info(f"Found {len(settings)} users with sync enabled")
                
                for setting in settings:
                    user = User.query.get(setting.user_id)
                    
                    # Skip if user is not premium
                    if not user.is_premium:
                        logger.info(f"Skipping non-premium user {user.username}")
                        continue
                        
                    # Check if it's time to sync based on frequency
                    should_sync = False
                    
                    if setting.last_sync is None:
                        should_sync = True
                    elif setting.frequency == 'hourly' and (now - setting.last_sync).total_seconds() >= 3600:
                        should_sync = True
                    elif setting.frequency == 'daily' and (now - setting.last_sync).total_seconds() >= 86400:
                        should_sync = True
                    elif setting.frequency == 'weekly' and (now - setting.last_sync).total_seconds() >= 604800:
                        should_sync = True
                        
                    if should_sync:
                        logger.info(f"Starting sync for user {user.username}")
                        try:
                            # Initialize API clients for the user
                            canvas_api_client = CanvasAPI(
                                api_url=user.canvas_api_url,
                                api_token=user.get_canvas_api_token()
                            )
                            todoist_client = TodoistClient(
                                api_token=user.get_todoist_api_key()
                            )
                            sync_service_client = SyncService(canvas_api_client, todoist_client)
                            
                            # Get all courses
                            courses = canvas_api_client.get_courses()
                            
                            # Sync assignments for each course
                            synced_count = 0
                            for course in courses:
                                tasks = sync_service_client.sync_course_assignments(course['id'])
                                synced_count += len(tasks)
                            
                            # Update last sync time
                            setting.last_sync = now
                            db.session.commit()
                            
                            # Record successful sync
                            history = SyncHistory(
                                user_id=user.id,
                                sync_type='scheduled',
                                source_id='all_courses',
                                items_count=synced_count,
                                status='success'
                            )
                            db.session.add(history)
                            db.session.commit()
                            
                            logger.info(f"Sync completed for user {user.username}: {synced_count} items synced")
                        except Exception as e:
                            logger.error(f"Error syncing for user {user.username}: {str(e)}")
                            
                            # Record failed sync
                            history = SyncHistory(
                                user_id=user.id,
                                sync_type='scheduled',
                                source_id='all_courses',
                                status='failed'
                            )
                            db.session.add(history)
                            db.session.commit()
                
                logger.info("Scheduled sync job completed")
            finally:
                # Ensure database sessions are properly closed
                db.session.remove()
                # Dispose of the engine connections
                db.engine.dispose()
                logger.info("Database connections cleaned up")
    
    except Exception as e:
        logger.error(f"Error in scheduler: {str(e)}")

if __name__ == "__main__":
    main() 