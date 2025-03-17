"""
Test script to check all registered routes in the application.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the application
from app import app

# Print all registered routes
print("All registered routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule.rule} -> {rule.endpoint}")

# Specifically check for the root route
root_routes = [rule for rule in app.url_map.iter_rules() if rule.rule == '/']
print("\nRoot routes:")
for rule in root_routes:
    print(f"{rule.rule} -> {rule.endpoint}")

# Print blueprint info
print("\nRegistered blueprints:")
for blueprint_name, blueprint in app.blueprints.items():
    print(f"{blueprint_name}: url_prefix={blueprint.url_prefix}") 