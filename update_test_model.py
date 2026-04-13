#!/usr/bin/env python
"""
Update Test model to allow nullable subject_id
"""

import sqlite3
from app import app

def update_test_model():
    """Update test table to allow nullable subject_id"""
    db_path = 'education.db'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create new table with nullable subject_id
        cursor.execute('''
        CREATE TABLE test_new (
            id INTEGER PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            subject_id INTEGER,
            is_daily BOOLEAN DEFAULT 0,
            is_comprehensive BOOLEAN DEFAULT 0,
            is_dtm BOOLEAN DEFAULT 0,
            test_date DATETIME,
            start_time DATETIME,
            end_time DATETIME,
            duration_minutes INTEGER DEFAULT 60,
            FOREIGN KEY (subject_id) REFERENCES subject (id)
        )
        ''')
        
        # Copy data from old table
        cursor.execute('''
        INSERT INTO test_new (id, title, subject_id, is_daily, is_comprehensive, is_dtm, test_date, start_time, end_time, duration_minutes)
        SELECT id, title, subject_id, is_daily, is_comprehensive, is_dtm, test_date, start_time, end_time, duration_minutes
        FROM test
        ''')
        
        # Drop old table
        cursor.execute('DROP TABLE test')
        
        # Rename new table
        cursor.execute('ALTER TABLE test_new RENAME TO test')
        
        conn.commit()
        print("Test model successfully updated!")
        
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_test_model()
