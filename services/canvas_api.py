import os
import requests
from dotenv import load_dotenv
import logging

load_dotenv()

class CanvasAPI:
    def __init__(self, api_url=None, api_token=None):
        env_url = os.getenv('CANVAS_API_URL')
        env_token = os.getenv('CANVAS_API_TOKEN')
        
        self.api_url = api_url or env_url
        self.api_token = api_token or env_token
        
        # Add more detailed validation
        if not self.api_url:
            raise ValueError("Canvas API URL must be provided")
        
        if not self.api_token:
            raise ValueError("Canvas API token must be provided")
        
        # Ensure the URL ends with /api/v1
        if not self.api_url.endswith('/api/v1'):
            # Try to fix the URL
            if self.api_url.endswith('/'):
                self.api_url = self.api_url + 'api/v1'
            else:
                self.api_url = self.api_url + '/api/v1'
            logging.info(f"Canvas API URL modified to include /api/v1: {self.api_url}")
        
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
        
        try:
            logging.info(f"Getting courses from Canvas API: {endpoint}")
            response = requests.get(endpoint, headers=self.headers, params=params)
            
            # If unauthorized, provide a helpful error
            if response.status_code == 401:
                raise ValueError("Unauthorized: Your Canvas API token appears to be invalid or expired")
            
            # If we get a different error, provide helpful information
            response.raise_for_status()
            
            data = response.json()
            if data and len(data) > 0:
                logging.info(f"First course data sample: {data[0]}")
            logging.info(f"Successfully fetched {len(data)} courses from Canvas")
            return data
        except requests.exceptions.ConnectionError:
            logging.error(f"Connection error when connecting to Canvas API at {endpoint}")
            raise ValueError(f"Could not connect to Canvas API. Please verify the URL {self.api_url} is correct.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request error when fetching courses: {str(e)}")
            raise
    
    def get_assignments(self, course_id):
        """Retrieve assignments for a specific course"""
        endpoint = f"{self.api_url}/courses/{course_id}/assignments"
        params = {
            'per_page': 100,
            'order_by': 'due_at',
            'include[]': 'submission'
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching assignments for course {course_id}: {str(e)}")
            raise
    
    def get_todo_items(self):
        """Retrieve user's to-do items from Canvas"""
        endpoint = f"{self.api_url}/users/self/todo"
        
        try:
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching todo items: {str(e)}")
            raise
