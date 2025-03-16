print("Importing sync_service")
from datetime import datetime
from .canvas_api import CanvasAPI
from .todoist_api import TodoistClient

class SyncService:
    def __init__(self, canvas_api=None, todoist_client=None):
        self.canvas_api = canvas_api or CanvasAPI()
        self.todoist_client = todoist_client or TodoistClient()
    
    def format_assignment_as_task(self, assignment, course_name=None):
        """Format a Canvas assignment as a Todoist task"""
        # Format the due date if available
        due_date = None
        if assignment.get('due_at'):
            due_datetime = datetime.fromisoformat(assignment['due_at'].replace('Z', '+00:00'))
            due_date = due_datetime.strftime('%Y-%m-%d')
        
        # Create task content with course name if available
        if course_name:
            content = f"[{course_name}] {assignment['name']}"
        else:
            content = assignment['name']
        
        # Add assignment URL as a note
        content += f" ({assignment['html_url']})"
        
        # Set priority based on points possible (if available)
        priority = 1  # Default priority
        if assignment.get('points_possible'):
            if assignment['points_possible'] > 50:
                priority = 4  # Highest priority
            elif assignment['points_possible'] > 25:
                priority = 3
            elif assignment['points_possible'] > 10:
                priority = 2
        
        return {
            'content': content,
            'due_date': due_date,
            'priority': priority,
            'labels': ['canvas']
        }
    
    def sync_course_assignments(self, course_id, project_id=None):
        """Sync assignments from a Canvas course to Todoist"""
        # Get course details to include course name in tasks
        courses = self.canvas_api.get_courses()
        course_name = None
        for course in courses:
            if str(course['id']) == str(course_id):
                course_name = course['name']
                break
        
        # Get assignments for the course
        assignments = self.canvas_api.get_assignments(course_id)
        
        # Create tasks in Todoist
        created_tasks = []
        for assignment in assignments:
            # Skip assignments that have been submitted
            if assignment.get('submission') and assignment['submission'].get('submitted_at'):
                continue
            
            # Format assignment as task
            task_data = self.format_assignment_as_task(assignment, course_name)
            
            # Add project_id if specified
            if project_id:
                task_data['project_id'] = project_id
            
            # Create task in Todoist
            task = self.todoist_client.create_task(**task_data)
            if task:
                created_tasks.append(task)
        
        return created_tasks
    
    def sync_todo_items(self, project_id=None):
        """Sync Canvas to-do items to Todoist"""
        # Get to-do items from Canvas
        todo_items = self.canvas_api.get_todo_items()
        
        # Create tasks in Todoist
        created_tasks = []
        for item in todo_items:
            # Extract assignment details
            assignment = item.get('assignment', {})
            
            # Format as task
            task_data = {
                'content': f"{item.get('context_name', 'Canvas')} - {item.get('title', 'Task')}",
                'labels': ['canvas', 'todo'],
                'priority': 3  # Medium-high priority
            }
            
            # Add due date if available
            if assignment.get('due_at'):
                due_datetime = datetime.fromisoformat(assignment['due_at'].replace('Z', '+00:00'))
                task_data['due_date'] = due_datetime.strftime('%Y-%m-%d')
            
            # Add project_id if specified
            if project_id:
                task_data['project_id'] = project_id
            
            # Create task in Todoist
            task = self.todoist_client.create_task(**task_data)
            if task:
                created_tasks.append(task)
        
        return created_tasks
