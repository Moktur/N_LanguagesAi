#!/usr/bin/env python3
"""
Main entry point for the N-LanguagesAI application
"""
import os
import sys


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from app import create_app

def main():
    """Main application entry point"""
    # create Flask-App
    app = create_app()
    
    # staaart
    print("🚀 Starting N-LanguagesAI Server...")
    print(f"📊 API Documentation available at: http://localhost:5002/apidocs")
    print(f"🌍 Server running on: http://localhost:5002")
    print("⏹️  Press CTRL+C to stop the server")
    
    app.run(
        host="0.0.0.0", 
        port=5002, 
        debug=True,
        use_reloader=True
    )

if __name__ == '__main__':
    main()