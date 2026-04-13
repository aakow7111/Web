import os
import sys
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
import random

# Add the parent directory to the path to import app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, Group, Subject, Test, Question, Topic
from dtm_test_bank import ALL_DTM_QUESTIONS

def create_auto_test_schedule():
    """Create automatic test schedule starting from 13.04.2026"""
    print("Creating automatic test schedule...")
    
    # Start date
    start_date = datetime(2026, 4, 13)
    
    # Define subjects for each day of the week
    subjects_schedule = [
        'Huquq',         # Day 1 - Dushanba
        'Ingliz tili',   # Day 2 - Seshanba
        'DTM',           # Day 3 - Chorshanba (DTM)
        'Tarix',         # Day 4 - Payshanba
        'Ona tili',      # Day 5 - Juma
        'DTM',           # Day 6 - Shanba (DTM)
        'Matematika'     # Day 7 - Yakshanba
    ]
    
    # DTM test days (2 times in 7 days)
    dtm_days = [2, 5]  # Days 3 and 6 (0-indexed) - Chorshanba va Shanba
    
    # Create tests for 7 days
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        
        # Determine if this is a DTM test day (2 times in 7 days)
        is_dtm_day = day_offset in dtm_days
        
        # Select subject for this day
        subject_name = subjects_schedule[day_offset]
        
        # Create test
        if is_dtm_day:
            create_dtm_test(current_date)
        else:
            create_daily_test(current_date, subject_name)
    
    print("Test schedule created successfully!")

def create_daily_test(date, subject_name):
    """Create a daily test with 30 questions"""
    subject = Subject.query.filter_by(name=subject_name).first()
    if not subject:
        print(f"No subject found: {subject_name}")
        return
    
    # Create test
    test = Test(
        title=f"Kunlik Test - {subject_name} ({date.strftime('%d.%m.%Y')})",
        subject_id=subject.id,
        test_date=date,
        is_daily=True,
        duration_minutes=45  # 30 savol uchun 45 daqiqa
    )
    
    db.session.add(test)
    db.session.commit()
    
    print(f"Created Daily test for {subject_name} on {date.strftime('%d.%m.%Y')}")
    
    # Add 30 questions
    add_dtm_questions_to_test(test.id, subject_name, 30)

def create_dtm_test(date):
    """Create a general DTM test with 90 questions from 5 subjects"""
    # Create test without subject
    test_date_with_time = datetime.combine(date, datetime.min.time())
    start_time = datetime.combine(date, datetime.strptime('18:00', '%H:%M').time())
    end_time = datetime.combine(date, datetime.strptime('20:00', '%H:%M').time())
    
    test = Test(
        title=f"DTM Test ({date.strftime('%d.%m.%Y')})",
        subject_id=None,  # No subject for DTM tests
        test_date=test_date_with_time,
        start_time=start_time,
        end_time=end_time,
        is_daily=False,
        duration_minutes=120  # 90 savol uchun 2 soat
    )
    
    db.session.add(test)
    db.session.commit()
    
    print(f"Created general DTM test on {date.strftime('%d.%m.%Y')}")
    
    # Add 90 questions
    add_dtm_questions_to_test(test.id, None, 90)

def add_dtm_questions_to_test(test_id, subject_name, question_count):
    """Add DTM format questions to a test"""
    if question_count == 90:
        # DTM test with TDYU entrance exam subjects: Huquq(30), Ingliz tili(30), Tarix(10), Ona tili(10), Matematika(10)
        subject_distribution = {
            'Huquq': 30,
            'Ingliz tili': 30,
            'Tarix': 10,
            'Ona tili': 10,
            'Matematika': 10
        }
        
        for subj_name, count in subject_distribution.items():
            subject_questions = ALL_DTM_QUESTIONS.get(subj_name, [])
            
            if not subject_questions:
                print(f"No DTM questions found for subject: {subj_name}")
                continue
            
            # If we need more questions than available, repeat some questions
            questions_to_add = []
            while len(questions_to_add) < count:
                questions_to_add.extend(subject_questions)
            
            # Randomly select the required number of questions
            selected_questions = random.sample(questions_to_add, count)
            
            for q_data in selected_questions:
                # Convert options dict to pipe-separated format
                option_values = []
                for key in ['A', 'B', 'C', 'D']:
                    if key in q_data['options']:
                        option_values.append(q_data['options'][key])
                    else:
                        option_values.append(f"Option {key}")
                
                question = Question(
                    test_id=test_id,
                    question_text=f"[{subj_name}] {q_data['question']}",
                    correct_answer=q_data['correct'],
                    options='|'.join(option_values)  # Pipe-separated format
                )
                
                db.session.add(question)
        
        db.session.commit()
        print(f"Added 90 DTM questions (5 subjects) to test {test_id}")
        
    else:
        # Daily test with single subject
        subject_questions = ALL_DTM_QUESTIONS.get(subject_name, [])
        
        if not subject_questions:
            print(f"No DTM questions found for subject: {subject_name}")
            return
        
        # If we need more questions than available, repeat some questions
        questions_to_add = []
        while len(questions_to_add) < question_count:
            questions_to_add.extend(subject_questions)
        
        # Randomly select the required number of questions
        selected_questions = random.sample(questions_to_add, question_count)
        
        for i, q_data in enumerate(selected_questions):
            # Convert options dict to pipe-separated format
            option_values = []
            for key in ['A', 'B', 'C', 'D']:
                if key in q_data['options']:
                    option_values.append(q_data['options'][key])
                else:
                    option_values.append(f"Option {key}")
            
            question = Question(
                test_id=test_id,
                question_text=q_data['question'],
                correct_answer=q_data['correct'],
                options='|'.join(option_values)  # Pipe-separated format
            )
            
            db.session.add(question)
        
        db.session.commit()
        print(f"Added {question_count} DTM questions to test {test_id}")

def update_weekly_schedule():
    """Update schedule weekly"""
    print("Updating weekly schedule...")
    
    # Get the latest test date
    latest_test = Test.query.order_by(Test.test_date.desc()).first()
    if not latest_test:
        print("No tests found, creating initial schedule...")
        create_auto_test_schedule()
        return
    
    # Create tests for the next 7 days
    start_date = latest_test.test_date + timedelta(days=1)
    
    # Continue the 7-day pattern (DTM entrance exam subjects only)
    subjects_schedule = [
        'Tarix',         # Next day pattern continues
        'Matematika',    
        'Ona tili',      
        'Ingliz tili',   
        'Tarix',         
        'Matematika',    
        'Ona tili'      
    ]
    
    for day_offset in range(7):
        current_date = start_date + timedelta(days=day_offset)
        
        # Determine if this is a DTM test day (every 3rd day)
        is_dtm_day = day_offset in [0, 3, 6]  # Adjusted for weekly pattern
        
        # Select subject for this day
        subject_name = subjects_schedule[day_offset]
        
        # Create test
        if is_dtm_day:
            create_dtm_test(current_date, subject_name)
        else:
            create_daily_test(current_date, subject_name)
    
    print("Weekly schedule updated!")

def create_single_day_test(date, subject_name, is_dtm=False):
    """Create a test for a single day"""
    subject = Subject.query.filter_by(name=subject_name).first()
    if not subject:
        print(f"No subject found: {subject_name}")
        return
    
    # Create test
    test_title = f"DTM Test - {subject_name} ({date.strftime('%d.%m.%Y')})" if is_dtm else f"Kunlik Test - {subject_name} ({date.strftime('%d.%m.%Y')})"
    question_count = 90 if is_dtm else 30
    duration = 120 if is_dtm else 45
    
    test = Test(
        title=test_title,
        subject_id=subject.id,
        test_date=date,
        is_daily=not is_dtm,
        duration_minutes=duration
    )
    
    db.session.add(test)
    db.session.commit()
    
    print(f"Created {'DTM' if is_dtm else 'Daily'} test for {subject_name} on {date.strftime('%d.%m.%Y')}")
    
    # Add questions
    add_dtm_questions_to_test(test.id, subject_name, question_count)

def create_extended_schedule():
    """Create extended schedule for multiple weeks"""
    print("Creating extended schedule...")
    
    # Start date
    start_date = datetime(2026, 4, 13)
    
    # Define subjects for 7-day pattern (DTM entrance exam subjects only)
    subjects_schedule = [
        'Matematika',    # Day 1
        'Ona tili',      # Day 2
        'Ingliz tili',   # Day 3 (DTM)
        'Tarix',         # Day 4
        'Matematika',    # Day 5
        'Ona tili',      # Day 6 (DTM)
        'Ingliz tili'    # Day 7 (DTM)
    ]
    
    # Create tests for 4 weeks (28 days)
    for week in range(4):
        for day_offset in range(7):
            current_date = start_date + timedelta(days=week*7 + day_offset)
            
            # Determine if this is a DTM test day
            is_dtm_day = day_offset in [2, 5, 6]  # Days 3, 6, 7
            
            # Select subject for this day
            subject_name = subjects_schedule[day_offset]
            
            # Create test
            if is_dtm_day:
                create_dtm_test(current_date)
            else:
                create_daily_test(current_date, subject_name)
    
    print("Extended schedule created successfully!")

if __name__ == "__main__":
    with app.app_context():
        # Clear existing tests
        Test.query.delete()
        Question.query.delete()
        db.session.commit()
        
        # Create new extended schedule
        create_extended_schedule()
    print("Test schedule created successfully!")
