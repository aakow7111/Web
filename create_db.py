#!/usr/bin/env python
"""
Create database with updated Test model
"""

from app import app, db

def create_database():
    """Create database with updated Test model"""
    with app.app_context():
        db.create_all()
        print("Database created successfully!")

if __name__ == "__main__":
    create_database()
