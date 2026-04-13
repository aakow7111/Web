import sqlite3
import os

def migrate_database():
    db_path = 'instance/education.db'
    
    if not os.path.exists(db_path):
        print("Ma'lumotlar bazasi mavjud emas. Dasturni qayta ishga tushiring.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if is_dtm column exists
        cursor.execute("PRAGMA table_info(test)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print("Joriy ustunlar:", columns)
        
        # Add missing columns
        if 'is_dtm' not in columns:
            print("is_dtm ustuni qo'shilmoqda...")
            cursor.execute("ALTER TABLE test ADD COLUMN is_dtm BOOLEAN DEFAULT 0")
        
        if 'start_time' not in columns:
            print("start_time ustuni qo'shilmoqda...")
            cursor.execute("ALTER TABLE test ADD COLUMN start_time DATETIME")
        
        if 'end_time' not in columns:
            print("end_time ustuni qo'shilmoqda...")
            cursor.execute("ALTER TABLE test ADD COLUMN end_time DATETIME")
        
        if 'duration_minutes' not in columns:
            print("duration_minutes ustuni qo'shilmoqda...")
            cursor.execute("ALTER TABLE test ADD COLUMN duration_minutes INTEGER DEFAULT 60")
        
        # Check if knowledge_level table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_level'")
        if not cursor.fetchone():
            print("knowledge_level jadvali yaratilmoqda...")
            cursor.execute('''
                CREATE TABLE knowledge_level (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    level INTEGER DEFAULT 0,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (student_id) REFERENCES user (id),
                    FOREIGN KEY (subject_id) REFERENCES subject (id)
                )
            ''')
        
        # Check if test_registration table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_registration'")
        if not cursor.fetchone():
            print("test_registration jadvali yaratilmoqda...")
            cursor.execute('''
                CREATE TABLE test_registration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    test_id INTEGER NOT NULL,
                    registration_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    attended BOOLEAN DEFAULT 0,
                    FOREIGN KEY (student_id) REFERENCES user (id),
                    FOREIGN KEY (test_id) REFERENCES test (id)
                )
            ''')
        
        # Add new columns to user table if they don't exist
        cursor.execute("PRAGMA table_info(user)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_group_leader' not in columns:
            print("is_group_leader ustuni qo'shilmoqda...")
            cursor.execute("ALTER TABLE user ADD COLUMN is_group_leader BOOLEAN DEFAULT 0")
        
        if 'needs_password_change' not in columns:
            print("needs_password_change ustuni qo'shilmoqda...")
            cursor.execute("ALTER TABLE user ADD COLUMN needs_password_change BOOLEAN DEFAULT 0")
        
        conn.commit()
        print("Migratsiya muvaffaqiyatli yakunlandi!")
        
    except Exception as e:
        print(f"Xatolik: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
