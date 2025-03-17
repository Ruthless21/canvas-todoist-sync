#!/usr/bin/env python3
"""
Canvas API Testing Script
This script will help diagnose issues with your Canvas API connection.
"""

import os
import sys
import json
import requests
from datetime import datetime

# ANSI color codes for terminal output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_header(text):
    """Print a section header"""
    print(f"\n{BLUE}{BOLD}{'=' * 70}{RESET}")
    print(f"{BLUE}{BOLD}= {text}{' ' * (67 - len(text))}={RESET}")
    print(f"{BLUE}{BOLD}{'=' * 70}{RESET}")

def print_success(message):
    """Print a success message"""
    print(f"{GREEN}✓ {message}{RESET}")

def print_warning(message):
    """Print a warning message"""
    print(f"{YELLOW}⚠ {message}{RESET}")

def print_error(message):
    """Print an error message"""
    print(f"{RED}✖ {message}{RESET}")

def print_info(message):
    """Print an info message"""
    print(f"{BLUE}ℹ {message}{RESET}")

def test_canvas_api(api_url, api_token):
    """Test the Canvas API connection with the provided credentials"""
    print_header("Testing Canvas API Connection")
    print_info(f"Testing connection to: {api_url}")

    # Step 1: Validate URL format
    if not api_url:
        print_error("Canvas API URL is empty")
        print_info("Please provide a valid Canvas API URL")
        return False

    # Check if the URL ends with /api/v1
    original_url = api_url
    if not api_url.endswith('/api/v1'):
        # Try to fix the URL
        if api_url.endswith('/'):
            api_url = api_url + 'api/v1'
        else:
            api_url = api_url + '/api/v1'
        print_warning(f"Canvas API URL modified to include /api/v1: {api_url}")

    # Check if the token is empty
    if not api_token:
        print_error("Canvas API token is empty")
        print_info("Please provide a valid Canvas API token")
        return False

    # Step 2: Test the connection
    try:
        headers = {
            'Authorization': f'Bearer {api_token}'
        }
        
        # First try a simple test endpoint
        print_info("Testing API connection with user profile endpoint...")
        user_endpoint = f"{api_url}/users/self/profile"
        response = requests.get(user_endpoint, headers=headers)
        
        # Check response status
        if response.status_code == 200:
            user_data = response.json()
            print_success(f"Successfully connected to Canvas API as: {user_data.get('name', 'Unknown user')}")
            
            # Fetch available courses
            print_info("Fetching courses...")
            courses_endpoint = f"{api_url}/courses"
            params = {
                'enrollment_state': 'active',
                'per_page': 100
            }
            courses_response = requests.get(courses_endpoint, headers=headers, params=params)
            
            if courses_response.status_code == 200:
                courses = courses_response.json()
                if courses:
                    print_success(f"Successfully retrieved {len(courses)} courses:")
                    for i, course in enumerate(courses[:5]):  # Show only the first 5 courses
                        print(f"  {i+1}. {course.get('name', 'Unknown course')}")
                    
                    if len(courses) > 5:
                        print_info(f"... and {len(courses) - 5} more courses")
                else:
                    print_warning("No active courses found in your Canvas account")
                
                return True
            else:
                print_error(f"Failed to retrieve courses (HTTP {courses_response.status_code})")
                print_info(f"Response: {courses_response.text[:500]}")
                return False
        elif response.status_code == 401:
            print_error("Authentication failed (HTTP 401 Unauthorized)")
            print_info("Your Canvas API token appears to be invalid or expired")
            return False
        elif response.status_code == 404:
            print_error("API endpoint not found (HTTP 404 Not Found)")
            print_info("This may indicate that the URL is incorrect")
            # Try without /api/v1 to see if that works
            if '/api/v1' in api_url:
                base_url = api_url.replace('/api/v1', '')
                print_info(f"Trying alternative URL without /api/v1: {base_url}")
                return test_canvas_api(base_url, api_token)
            return False
        else:
            print_error(f"Unexpected status code: {response.status_code}")
            print_info(f"Response: {response.text[:500]}")
            return False
    except requests.exceptions.ConnectionError:
        print_error("Connection error")
        print_info(f"Could not connect to Canvas API at {api_url}")
        print_info("Please check your network connection and Canvas API URL")
        return False
    except requests.exceptions.RequestException as e:
        print_error(f"Request error: {str(e)}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return False

def main():
    """Main function - gets credentials and tests the API"""
    print_header("Canvas API Testing Tool")
    print(f"This script will help diagnose issues with your Canvas API connection.")
    print(f"Run this on PythonAnywhere to test your Canvas credentials.")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get Canvas API URL from command line or prompt
    if len(sys.argv) > 1:
        canvas_api_url = sys.argv[1]
    else:
        canvas_api_url = input("\nEnter your Canvas API URL (e.g. https://canvas.instructure.com): ")
    
    # Get Canvas API token from command line or prompt
    if len(sys.argv) > 2:
        canvas_api_token = sys.argv[2]
    else:
        canvas_api_token = input("Enter your Canvas API token: ")
    
    # Run the test
    success = test_canvas_api(canvas_api_url, canvas_api_token)
    
    # Print recommendations
    print_header("Recommendations")
    
    if success:
        print_success("Your Canvas API connection is working correctly.")
        print_info("To update your application with these credentials:")
        print("1. Make sure the Canvas API URL is correct in your application")
        print("   - API URL should end with /api/v1")
        print("2. Pull the latest changes from git:")
        print("   cd ~/canvas-todoist-sync")
        print("   git pull origin main")
        print("3. Reload your web app from the PythonAnywhere dashboard")
    else:
        print_error("Your Canvas API connection is not working correctly.")
        print_info("Common issues to check:")
        print("1. Make sure the Canvas API URL is correct (should end with /api/v1)")
        print("2. Verify your Canvas API token is valid and not expired")
        print("3. Check if your Canvas instance requires additional authentication")
        print("4. Pull the latest changes from git:")
        print("   cd ~/canvas-todoist-sync")
        print("   git pull origin main")
        print("5. Reload your web app from the PythonAnywhere dashboard")

if __name__ == "__main__":
    main() 