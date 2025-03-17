# This file can be empty or contain package initialization code

"""
Services package.
Contains API integration services for Canvas and Todoist.
"""

import requests
import logging
from datetime import datetime
from ..utils import logger

class CanvasAPI:
    """Canvas LMS API client."""
    
    def __init__(self, api_url, api_token):
        """Initialize Canvas API client."""
        self.api_url = api_url.rstrip('/')
        if not self.api_url.endswith('/api/v1'):
            self.api_url = f"{self.api_url}/api/v1"
        
        self.api_token = api_token
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make API request to Canvas."""
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Canvas API request failed: {str(e)}")
            raise
    
    def get_courses(self):
        """Get user's courses."""
        return self._make_request('GET', '/courses')
    
    def get_assignments(self):
        """Get user's assignments."""
        return self._make_request('GET', '/users/self/upcoming_events')
    
    def get_todo_items(self):
        """Get user's todo items."""
        return self._make_request('GET', '/users/self/todo')

class TodoistAPI:
    """Todoist API client."""
    
    def __init__(self, api_token):
        """Initialize Todoist API client."""
        self.api_token = api_token
        self.base_url = 'https://api.todoist.com/rest/v2'
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make API request to Todoist."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Todoist API request failed: {str(e)}")
            raise
    
    def get_projects(self):
        """Get user's projects."""
        return self._make_request('GET', '/projects')
    
    def get_tasks(self):
        """Get user's tasks."""
        return self._make_request('GET', '/tasks')
    
    def create_task(self, content, project_id=None, due_string=None):
        """Create a new task."""
        data = {'content': content}
        if project_id:
            data['project_id'] = project_id
        if due_string:
            data['due_string'] = due_string
        
        return self._make_request('POST', '/tasks', json=data)
    
    def update_task(self, task_id, **kwargs):
        """Update an existing task."""
        return self._make_request('POST', f'/tasks/{task_id}', json=kwargs)
    
    def delete_task(self, task_id):
        """Delete a task."""
        return self._make_request('DELETE', f'/tasks/{task_id}')
    
    def clear_tasks(self):
        """Clear all tasks."""
        tasks = self.get_tasks()
        for task in tasks:
            self.delete_task(task['id'])
        return True