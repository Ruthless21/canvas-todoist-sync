import os
import requests
from dotenv import load_dotenv

load_dotenv()

class CanvasAPI:
    def __init__(self, api_url=None, api_token=None):
        env_url = os.getenv('CANVAS_API_URL')
        env_token = os.getenv('CANVAS_API_TOKEN')
        
        self.api_url = api_url or env_url
        self.api_token = api_token or env_token
        
        if not self.api_url or not self.api_token:
            raise ValueError("Canvas API URL and token must be provided or set in environment variables")
        
        self.headers = {
            'Authorization': f'Bearer {self.api_token}'
        }
    
    def get_courses(self, enrollment_state='active'):
        """Retrieve user's courses from Canvas"""
        endpoint = f"{self.api_url}/courses"
        params = {
            'enrollment_state': enrollment_state,
            'per_page': 100
        }
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_assignments(self, course_id):
        """Retrieve assignments for a specific course"""
        endpoint = f"{self.api_url}/courses/{course_id}/assignments"
        params = {
            'per_page': 100,
            'order_by': 'due_at',
            'include[]': 'submission'
        }
        
        response = requests.get(endpoint, headers=self.headers, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_todo_items(self):
        """Retrieve user's to-do items from Canvas"""
        endpoint = f"{self.api_url}/users/self/todo"
        
        response = requests.get(endpoint, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
