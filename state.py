# state.py
"""
Global State Management

This module provides a central location for managing global state in the application.
It initializes and exports a shared user instance that can be imported by other modules.
"""

from models.user import User

# Initialize a shared user instance for global state management
user = User()
