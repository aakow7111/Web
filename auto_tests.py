import sqlite3
from datetime import datetime, timedelta
import random

def create_daily_tests():
    """Har kuni faqat bitta fan bo'yicha test yaratish (kunlik aylanish)"""
    db_path = 'instance/education.db'
    
    # Fanlar ro'yxati (kunlik aylanish uchun)
    subjects_rotation = ['Huquq', 'Ingliz tili', 'Tarix', 'Ona tili', 'Matematika']
    
    subjects_data = [
        {'name': 'Huquq', 'description': 'O\'zbekiston Respublikasi huquqi asoslari'},
        {'name': 'Ingliz tili', 'description': 'Ingliz tili grammatikasi va lug\'ati'},
        {'name': 'Tarix', 'description': 'O\'zbekiston va jahon tarixi'},
        {'name': 'Ona tili', 'description': 'O\'zbek tili grammatikasi va adabiyoti'},
        {'name': 'Matematika', 'description': 'Matematikaning asosiy bo\'limlari'}
    ]
    
    # Bugungi kun uchun fanni aniqlash (hafta kuniga qarab)
    today = datetime.now()
    weekday = today.weekday()  # 0 = Monday, 6 = Sunday
    
    # Hafta kunlariga qarab fanlarni tanlash (5 kunlik aylanish)
    subject_index = weekday % 5  # 0-4
    today_subject = subjects_rotation[subject_index]
    
    # Savollar to'plami
    questions_data = {
        'Huquq': [
            {
                'question': 'O\'zbekiston Respublikasi Konstitutsiyasi qachon qabul qilingan?',
                'options': '1991-yil 31-avgust|1992-yil 8-dekabr|1995-yil 25-dekabr|2000-yil 1-yanvar',
                'correct': '1992-yil 8-dekabr'
            },
            {
                'question': 'O\'zbekiston Respublikasining poytaxti qaysi shahar?',
                'options': 'Samarqand|Buxoro|Toshkent|Farg\'ona',
                'correct': 'Toshkent'
            },
            {
                'question': 'O\'zbekiston Respublikasida davlat tili qaysi til?',
                'options': 'Rus tili|Ingliz tili|O\'zbek tili|Qoraqalpoq tili',
                'correct': 'O\'zbek tili'
            }
        ],
        'Ingliz tili': [
            {
                'question': 'I ___ to school every day.',
                'options': 'go|goes|going|went',
                'correct': 'go'
            },
            {
                'question': 'She ___ a teacher.',
                'options': 'am|is|are|be',
                'correct': 'is'
            },
            {
                'question': 'They ___ playing football now.',
                'options': 'is|are|am|be',
                'correct': 'are'
            }
        ],
        'Tarix': [
            {
                'question': 'Amir Temur qachon tug\'ilgan?',
                'options': '1336-yil|1346-yil|1356-yil|1366-yil',
                'correct': '1336-yil'
            },
            {
                'question': 'Buyuk Ipak yo\'i qaysi davrlarda rivojlangan?',
                'options': 'Qadimgi davr|O\'rta asrlar|Yangi davr|Zamonaviy davr',
                'correct': 'Qadimgi davr'
            }
        ],
        'Ona tili': [
            {
                'question': '"O\'zbekiston" so\'zida nechta harf bor?',
                'options': '8|9|10|11',
                'correct': '10'
            },
            {
                'question': 'O\'zbek alifbosida nechta harf bor?',
                'options': '26|29|32|34',
                'correct': '29'
            }
        ],
        'Matematika': [
            {
                'question': '2 + 2 = ?',
                'options': '3|4|5|6',
                'correct': '4'
            },
            {
                'question': '10 × 10 = ?',
                'options': '90|100|110|120',
                'correct': '100'
            },
            {
                'question': '100 ÷ 4 = ?',
                'options': '20|25|30|35',
                'correct': '25'
            }
        ]
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Faqat bugungi fan uchun test yaratish
        subject_data = next((s for s in subjects_data if s['name'] == today_subject), None)
        
        if subject_data:
            # Fan ID sini topish
            cursor.execute("SELECT id FROM subject WHERE name = ?", (subject_data['name'],))
            subject = cursor.fetchone()
            
            if not subject:
                cursor.execute("""
                    INSERT INTO subject (name, description) 
                    VALUES (?, ?)
                """, (subject_data['name'], subject_data['description']))
                subject_id = cursor.lastrowid
                print(f"Fan qo'shildi: {subject_data['name']}")
            else:
                subject_id = subject[0]
            
            # Bugungi kun uchun test yaratish
            test_date = today.replace(hour=9, minute=0, second=0, microsecond=0)
            
            # Test mavjudligini tekshirish
            cursor.execute("""
                SELECT id FROM test 
                WHERE subject_id = ? AND DATE(test_date) = DATE(?) AND is_daily = 1
            """, (subject_id, test_date.date()))
            
            if not cursor.fetchone():
                # Yangi test yaratish (30 ta savol, 1 soat)
                cursor.execute("""
                    INSERT INTO test (title, subject_id, is_daily, test_date, duration_minutes)
                    VALUES (?, ?, ?, ?, ?)
                """, (f"{subject_data['name']} - Kundalik test ({today.strftime('%d.%m.%Y')})",
                      subject_id, True, test_date, 60))
                
                test_id = cursor.lastrowid
                
                # 30 ta savol qo'shish (takrorlanishi mumkin)
                if subject_data['name'] in questions_data:
                    available_questions = questions_data[subject_data['name']]
                    # 30 ta savol uchun mavjud savollarni takrorlash
                    for i in range(30):
                        q_data = available_questions[i % len(available_questions)]
                        cursor.execute("""
                            INSERT INTO question (test_id, question_text, options, correct_answer)
                            VALUES (?, ?, ?, ?)
                        """, (test_id, q_data['question'], q_data['options'], q_data['correct']))
                
                print(f"Kundalik test yaratildi: {subject_data['name']} - {today.strftime('%d.%m.%Y')} (30 savol)")
            else:
                print(f"Bugungi kunlik test allaqachon mavjud: {subject_data['name']}")
        
        conn.commit()
        print("Kundalik testlar muvaffaqiyatli yaratildi!")
        return True
        
    except Exception as e:
        print(f"Xatolik: {e}")
        return False
    finally:
        conn.close()

def create_weekly_tests():
    """7 kunlik jadval asosida testlar yaratish (5 kunlik, 2 kun DTM)"""
    db_path = 'instance/education.db'
    
    # 7 kunlik jadval (0 = Monday, 6 = Sunday)
    weekly_schedule = [
        {'day': 0, 'type': 'daily', 'subject': 'Huquq'},        # Dushanba - Kundalik
        {'day': 1, 'type': 'daily', 'subject': 'Ingliz tili'},  # Seshanba - Kundalik  
        {'day': 2, 'type': 'dtm', 'subject': 'Matematika'},      # Chorshanba - DTM
        {'day': 3, 'type': 'daily', 'subject': 'Tarix'},         # Payshanba - Kundalik
        {'day': 4, 'type': 'daily', 'subject': 'Ona tili'},       # Juma - Kundalik
        {'day': 5, 'type': 'dtm', 'subject': 'Ingliz tili'},     # Shanba - DTM
        {'day': 6, 'type': 'daily', 'subject': 'Matematika'},    # Yakshanba - Kundalik
    ]
    
    # Fanlar ma'lumotlari
    subjects_data = {
        'Huquq': {'description': 'O\'zbekiston Respublikasi huquqi asoslari'},
        'Ingliz tili': {'description': 'Ingliz tili grammatikasi va lug\'ati'},
        'Tarix': {'description': 'O\'zbekiston va jahon tarixi'},
        'Ona tili': {'description': 'O\'zbek tili grammatikasi va adabiyoti'},
        'Matematika': {'description': 'Matematikaning asosiy bo\'limlari'}
    }
    
    # Savollar to'plami
    questions_data = {
        'Huquq': [
            {'question': 'O\'zbekiston Respublikasi Konstitutsiyasi qachon qabul qilingan?', 'options': '1991-yil 31-avgust|1992-yil 8-dekabr|1995-yil 25-dekabr|2000-yil 1-yanvar', 'correct': '1992-yil 8-dekabr'},
            {'question': 'O\'zbekiston Respublikasining poytaxti qaysi shahar?', 'options': 'Samarqand|Buxoro|Toshkent|Farg\'ona', 'correct': 'Toshkent'},
            {'question': 'O\'zbekiston Respublikasida davlat tili qaysi til?', 'options': 'Rus tili|Ingliz tili|O\'zbek tili|Qoraqalpoq tili', 'correct': 'O\'zbek tili'}
        ],
        'Ingliz tili': [
            {'question': 'I ___ to school every day.', 'options': 'go|goes|going|went', 'correct': 'go'},
            {'question': 'She ___ a teacher.', 'options': 'am|is|are|be', 'correct': 'is'},
            {'question': 'They ___ playing football now.', 'options': 'is|are|am|be', 'correct': 'are'}
        ],
        'Tarix': [
            {'question': 'Amir Temur qachon tug\'ilgan?', 'options': '1336-yil|1346-yil|1356-yil|1366-yil', 'correct': '1336-yil'},
            {'question': 'Buyuk Ipak yo\'i qaysi davrlarda rivojlangan?', 'options': 'Qadimgi davr|O\'rta asrlar|Yangi davr|Zamonaviy davr', 'correct': 'Qadimgi davr'}
        ],
        'Ona tili': [
            {'question': '"Mening Vatanim yurtim" she\'ri muallifi kim?', 'options': 'Abdulla Qodiriy|Abdulla Oripov|Erkin Vohidov|Zulfiya', 'correct': 'Abdulla Oripov'},
            {'question': '"O\'zbekiston" so\'zida nechta harf bor?', 'options': '8|9|10|11', 'correct': '10'}
        ],
        'Matematika': [
            {'question': '2 + 2 = ?', 'options': '3|4|5|6', 'correct': '4'},
            {'question': '10 × 10 = ?', 'options': '90|100|110|120', 'correct': '100'},
            {'question': '100 ÷ 4 = ?', 'options': '20|25|30|35', 'correct': '25'}
        ]
    }
    
    # DTM uchun qiyinroq savollar
    dtm_questions = {
        'Matematika': [
            {'question': 'Kvadrat tenglamani ildizlarini toping: x² - 5x + 6 = 0', 'options': 'x=2, x=3|x=1, x=6|x=-2, x=-3|x=0, x=5', 'correct': 'x=2, x=3'},
            {'question': 'Arifmetik progressiyaning birinchi hadi a1=3, ayirmasi d=2. 10-hadini toping.', 'options': '21|23|25|27', 'correct': '21'}
        ],
        'Ona tili': [
            {'question': '"Mening Vatanim yurtim" she\'ri muallifi kim?', 'options': 'Abdulla Qodiriy|Abdulla Oripov|Erkin Vohidov|Zulfiya', 'correct': 'Abdulla Oripov'}
        ],
        'Tarix': [
            {'question': 'Temuriylar davlati qachon tashkil topgan?', 'options': '1370-yil|1380-yil|1390-yil|1400-yil', 'correct': '1370-yil'}
        ],
        'Ingliz tili': [
            {'question': 'Choose the correct form: If I ___ rich, I would travel the world.', 'options': 'am|is|were|will be', 'correct': 'were'}
        ],
        'Huquq': [
            {'question': 'O\'zbekiston Respublikasi Konstitutsiyasi nechta moddadan iborat?', 'options': '128|130|132|134', 'correct': '128'}
        ]
    }
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        today = datetime.now()
        current_weekday = today.weekday()
        
        # Bugungi kun uchun test yaratish
        today_schedule = next((s for s in weekly_schedule if s['day'] == current_weekday), None)
        
        if today_schedule:
            subject_name = today_schedule['subject']
            test_type = today_schedule['type']
            
            # Fan ID sini topish
            cursor.execute("SELECT id FROM subject WHERE name = ?", (subject_name,))
            subject = cursor.fetchone()
            
            if not subject:
                cursor.execute("INSERT INTO subject (name, description) VALUES (?, ?)", 
                             (subject_name, subjects_data[subject_name]['description']))
                subject_id = cursor.lastrowid
                print(f"Fan qo'shildi: {subject_name}")
            else:
                subject_id = subject[0]
            
            # Test mavjudligini tekshirish
            test_date = today.replace(hour=9, minute=0, second=0, microsecond=0)
            
            if test_type == 'daily':
                cursor.execute("""
                    SELECT id FROM test 
                    WHERE subject_id = ? AND DATE(test_date) = DATE(?) AND is_daily = 1
                """, (subject_id, test_date.date()))
            else:  # DTM
                cursor.execute("""
                    SELECT id FROM test 
                    WHERE subject_id = ? AND DATE(test_date) = DATE(?) AND is_dtm = 1
                """, (subject_id, test_date.date()))
            
            if not cursor.fetchone():
                if test_type == 'daily':
                    # Kundalik test (30 savol, 1 soat)
                    cursor.execute("""
                        INSERT INTO test (title, subject_id, is_daily, test_date, duration_minutes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (f"{subject_name} - Kundalik test ({today.strftime('%d.%m.%Y')})",
                          subject_id, True, test_date, 60))
                    
                    test_id = cursor.lastrowid
                    questions_to_add = questions_data[subject_name]
                    question_count = 30
                    
                else:  # DTM
                    # DTM test (90 savol, 1.5 soat)
                    end_time = test_date + timedelta(hours=1, minutes=30)
                    cursor.execute("""
                        INSERT INTO test (title, subject_id, is_dtm, test_date, duration_minutes, start_time, end_time)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (f"DTM Test - {subject_name} ({today.strftime('%d.%m.%Y')})",
                          subject_id, True, test_date, 90, test_date, end_time))
                    
                    test_id = cursor.lastrowid
                    questions_to_add = dtm_questions[subject_name]
                    question_count = 90
                
                # Savollarni qo'shish
                if questions_to_add:
                    for i in range(question_count):
                        q_data = questions_to_add[i % len(questions_to_add)]
                        cursor.execute("""
                            INSERT INTO question (test_id, question_text, options, correct_answer)
                            VALUES (?, ?, ?, ?)
                        """, (test_id, q_data['question'], q_data['options'], q_data['correct']))
                
                test_type_name = "Kundalik" if test_type == 'daily' else "DTM"
                print(f"{test_type_name} test yaratildi: {subject_name} - {today.strftime('%d.%m.%Y')} ({question_count} savol)")
            else:
                test_type_name = "Kundalik" if test_type == 'daily' else "DTM"
                print(f"Bugungi {test_type_name} test allaqachon mavjud: {subject_name}")
        
        conn.commit()
        print("Haftalik testlar muvaffaqiyatli yaratildi!")
        return True
        
    except Exception as e:
        print(f"Xatolik: {e}")
        return False
    finally:
        conn.close()

def create_dtm_tests():
    """Eski DTM testlar funktsiyasi (saqlab qolish uchun)"""
    return create_weekly_tests()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Foydalanish:")
        print("  python auto_tests.py daily    - Kundalik testlar yaratish")
        print("  python auto_tests.py dtm      - DTM testlar yaratish")
        print("  python auto_tests.py weekly   - Haftalik jadval bo'yicha testlar")
        print("  python auto_tests.py all      - Barcha testlar yaratish")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "daily":
        create_daily_tests()
    elif command == "dtm":
        create_dtm_tests()
    elif command == "weekly":
        create_weekly_tests()
    elif command == "all":
        create_weekly_tests()
    else:
        print("Noto'g'ri buyruq!")
