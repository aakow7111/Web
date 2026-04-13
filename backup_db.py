import sqlite3
import os
import shutil
from datetime import datetime
import json

def backup_database():
    """Ma'lumotlar bazasini zaxiralash"""
    db_path = 'instance/education.db'
    backup_dir = 'backups'
    
    # Create backup directory if it doesn't exist
    os.makedirs(backup_dir, exist_ok=True)
    
    if not os.path.exists(db_path):
        print("Ma'lumotlar bazasi mavjud emas!")
        return False
    
    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'education_backup_{timestamp}.db'
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Copy database file
        shutil.copy2(db_path, backup_path)
        
        # Create backup info file
        info = {
            'timestamp': timestamp,
            'filename': backup_filename,
            'original_size': os.path.getsize(db_path),
            'backup_size': os.path.getsize(backup_path)
        }
        
        info_path = os.path.join(backup_dir, f'backup_info_{timestamp}.json')
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        print(f"Zaxira muvaffaqiyatli yaratildi: {backup_path}")
        return True
        
    except Exception as e:
        print(f"Zaxiralashda xatolik: {e}")
        return False

def restore_database(backup_filename):
    """Ma'lumotlar bazasini tiklash"""
    backup_dir = 'backups'
    db_path = 'instance/education.db'
    backup_path = os.path.join(backup_dir, backup_filename)
    
    if not os.path.exists(backup_path):
        print(f"Zaxira fayli mavjud emas: {backup_filename}")
        return False
    
    try:
        # Create instance directory if it doesn't exist
        os.makedirs('instance', exist_ok=True)
        
        # Copy backup to original location
        shutil.copy2(backup_path, db_path)
        
        print(f"Ma'lumotlar bazasi muvaffaqiyatli tiklandi: {backup_filename}")
        return True
        
    except Exception as e:
        print(f"Tiklashda xatolik: {e}")
        return False

def list_backups():
    """Barcha zaxiralarni ro'yxatini ko'rsatish"""
    backup_dir = 'backups'
    
    if not os.path.exists(backup_dir):
        print("Zaxiralar papkasi mavjud emas!")
        return []
    
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.startswith('education_backup_') and filename.endswith('.db'):
            backup_path = os.path.join(backup_dir, filename)
            info_filename = filename.replace('.db', '.json')
            info_path = os.path.join(backup_dir, info_filename)
            
            backup_info = {
                'filename': filename,
                'size': os.path.getsize(backup_path),
                'created': datetime.fromtimestamp(os.path.getctime(backup_path))
            }
            
            # Load additional info if available
            if os.path.exists(info_path):
                try:
                    with open(info_path, 'r', encoding='utf-8') as f:
                        additional_info = json.load(f)
                        backup_info.update(additional_info)
                except:
                    pass
            
            backups.append(backup_info)
    
    # Sort by creation date (newest first)
    backups.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return backups

def cleanup_old_backups(keep_count=10):
    """Eski zaxiralarni tozalash (oxirgi keep_count tasini qoldirib qolganini o'chirish)"""
    backups = list_backups()
    
    if len(backups) <= keep_count:
        print("Tozalash uchun eski zaxiralar yo'q.")
        return
    
    backup_dir = 'backups'
    backups_to_delete = backups[keep_count:]
    
    for backup in backups_to_delete:
        backup_path = os.path.join(backup_dir, backup['filename'])
        info_path = os.path.join(backup_dir, backup['filename'].replace('.db', '.json'))
        
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
            if os.path.exists(info_path):
                os.remove(info_path)
            print(f"O'chirildi: {backup['filename']}")
        except Exception as e:
            print(f"O'chirishda xatolik {backup['filename']}: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Foydalanish:")
        print("  python backup_db.py backup          - Yangi zaxira yaratish")
        print("  python backup_db.py restore <file>  - Zaxiradan tiklash")
        print("  python backup_db.py list            - Zaxiralar ro'yxati")
        print("  python backup_db.py cleanup         - Eski zaxiralarni tozalash")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "backup":
        backup_database()
    elif command == "restore":
        if len(sys.argv) < 3:
            print("Tiklash uchun fayl nomini ko'rsating!")
            sys.exit(1)
        restore_database(sys.argv[2])
    elif command == "list":
        backups = list_backups()
        if backups:
            print("\nZaxiralar ro'yxati:")
            for i, backup in enumerate(backups, 1):
                timestamp = backup.get('timestamp', backup['created'].strftime('%Y%m%d_%H%M%S'))
                size_mb = backup['size'] / (1024 * 1024)
                print(f"{i}. {backup['filename']} - {timestamp} - {size_mb:.2f} MB")
        else:
            print("Zaxiralar mavjud emas.")
    elif command == "cleanup":
        cleanup_old_backups()
    else:
        print("Noto'g'ri buyruq!")
