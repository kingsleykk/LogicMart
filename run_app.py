#!/usr/bin/env python3
"""
Simple script to run the LogicMart application
"""

import sys
import os
from main import App

if __name__ == "__main__":
    try:
        app = App()
        print("LogicMart Analytics System started successfully!")
        print("Application is running on a clean codebase.")
        app.mainloop()
    except Exception as e:
        print(f"Error starting application: {e}")
        sys.exit(1)
