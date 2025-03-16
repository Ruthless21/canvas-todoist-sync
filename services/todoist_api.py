print("Importing todoist_api")
import os
from todoist_api_python.api import TodoistAPI
from dotenv import load_dotenv

load_dotenv()

class TodoistClient:
    def __init__(self, api_token=None):
        env_token = os.getenv('TODOIST_API_KEY')
        
        # Debug logging for API initialization
        print(f"DEBUG - TodoistClient.__init__:")
        print(f"DEBUG - Provided api_token: {'None' if api_token is None else 'Has Value ('+str(len(api_token))+' chars)'}")
        print(f"DEBUG - Env TODOIST_API_KEY: {'None' if env_token is None else 'Has Value ('+str(len(env_token))+' chars)'}")
        
        self.api_token = api_token or env_token
        
        if not self.api_token:
            raise ValueError("Todoist API token must be provided or set in environment variables")
        
        print(f"DEBUG - Using token from: {'Parameter' if api_token else 'Environment'}")
        
        self.api = TodoistAPI(self.api_token)
    
    def create_task(self, content, due_date=None, project_id=None, priority=None, labels=None):
        """Create a new task in Todoist"""
        try:
            task = self.api.add_task(
                content=content,
                due_date=due_date,
                project_id=project_id,
                priority=priority,
                labels=labels
            )
            return task
        except Exception as error:
            print(f"Error creating Todoist task: {error}")
            return None
    
    def get_projects(self):
        """Get all projects from Todoist"""
        try:
            return self.api.get_projects()
        except Exception as error:
            print(f"Error getting Todoist projects: {error}")
            return []
