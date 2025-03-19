import os
from todoist_api_python.api import TodoistAPI
from dotenv import load_dotenv

load_dotenv()

class TodoistClient:
    def __init__(self, api_token=None):
        env_token = os.getenv('TODOIST_API_TOKEN')
        
        # Remove debug logging that exposes partial credentials
        
        self.api_token = api_token or env_token
        
        if not self.api_token:
            raise ValueError("Todoist API token must be provided or set in environment variables")
        
        self.api = TodoistAPI(self.api_token)
    
    def create_task(self, content, due_date=None, project_id=None, priority=None, labels=None, description=None):
        """Create a new task in Todoist"""
        try:
            task_args = {
                'content': content,
                'due_date': due_date,
                'project_id': project_id,
                'priority': priority,
                'labels': labels
            }
            
            # Filter out None values
            task_args = {k: v for k, v in task_args.items() if v is not None}
            
            # Create the task
            task = self.api.add_task(**task_args)
            
            # Add description as a comment if provided
            if description and task:
                self.api.add_comment(
                    task_id=task.id,
                    content=description
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

    def get_tasks(self, project_id=None):
        """Get tasks from Todoist, optionally filtered by project"""
        try:
            # If project_id is provided, filter tasks by project
            if project_id:
                return self.api.get_tasks(project_id=project_id)
            # Otherwise, get all tasks
            return self.api.get_tasks()
        except Exception as error:
            print(f"Error getting Todoist tasks: {error}")
            return []
