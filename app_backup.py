import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///education.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_group_leader = db.Column(db.Boolean, default=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    needs_password_change = db.Column(db.Boolean, default=False)  # For one-time password
    
    group = db.relationship('Group', backref='students')
    test_results = db.relationship('TestResult', backref='student', lazy=True)
    certificates = db.relationship('Certificate', backref='student', lazy=True)
    difficult_topics = db.relationship('DifficultTopic', backref='student', lazy=True)
    knowledge_levels = db.relationship('KnowledgeLevel', backref='student_knowledge_levels', lazy=True)
    test_registrations = db.relationship('TestRegistration', backref='student_registrations', lazy=True)

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    total_score = db.Column(db.Integer, default=0)
    
    schedules = db.relationship('Schedule', backref='group', lazy=True)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    topics = db.relationship('Topic', backref='subject', lazy=True)
    tests = db.relationship('Test', backref='subject', lazy=True)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    video_url = db.Column(db.String(500))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    
    difficult_topics = db.relationship('DifficultTopic', backref='topic', lazy=True)

class Test(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=True)
    is_daily = db.Column(db.Boolean, default=False)
    is_comprehensive = db.Column(db.Boolean, default=False)
    is_dtm = db.Column(db.Boolean, default=False)
    test_date = db.Column(db.DateTime, default=datetime.utcnow)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer, default=60)
    
    questions = db.relationship('Question', backref='test', lazy=True)
    results = db.relationship('TestResult', backref='test', lazy=True)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(500), nullable=False)
    options = db.Column(db.Text, nullable=False)  # JSON string of options

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6 (Monday-Sunday)
    time_slot = db.Column(db.String(50), nullable=False)
    
    subject = db.relationship('Subject', backref='schedules')

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(500))

class DifficultTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    marked_date = db.Column(db.DateTime, default=datetime.utcnow)

class KnowledgeLevel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    level = db.Column(db.Integer, default=0)  # 0-100
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    student = db.relationship('User', backref='student_knowledge_levels')
    subject = db.relationship('Subject', backref='subject_knowledge_levels')

class TestRegistration(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    attended = db.Column(db.Boolean, default=False)  # Whether student actually took the test
    
    student = db.relationship('User', backref='student_test_registrations')
    test = db.relationship('Test', backref='test_registrations')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        elif current_user.is_group_leader:
            if current_user.needs_password_change:
                return redirect(url_for('change_password'))
            return redirect(url_for('group_leader_dashboard'))
        else:
            return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            next_page = request.args.get('next')
            
            if user.is_admin:
                return redirect(next_page) if next_page else redirect(url_for('admin_dashboard'))
            elif user.is_group_leader:
                if user.needs_password_change:
                    flash('Iltimos, parolingizni o\'zgartiring!', 'info')
                    return redirect(url_for('change_password'))
                return redirect(next_page) if next_page else redirect(url_for('group_leader_dashboard'))
            else:
                return redirect(next_page) if next_page else redirect(url_for('student_dashboard'))
        else:
            flash('Login yoki parol noto\'g\'ri!', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        group_id = request.form['group_id']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Parollar mos kelmadi!', 'danger')
            return render_template('register.html')
        
        # Generate automatic login
        base_login = f"{first_name.lower()}.{last_name.lower()}"
        username = base_login
        counter = 1
        
        # Ensure unique username
        while User.query.filter_by(username=username).first():
            username = f"{base_login}{counter}"
            counter += 1
        
        # Create new student
        student = User(
            username=username,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            group_id=group_id,
            is_admin=False
        )
        
        db.session.add(student)
        db.session.commit()
        
        flash(f'Siz muvaffaqiyatli ro\'yxatdan o\'tdingiz!<br>Login: <strong>{username}</strong><br>Parol: Siz kiritgan parol', 'success')
        return redirect(url_for('login'))
    
    # Get all groups for selection
    groups = Group.query.all()
    return render_template('register.html', groups=groups)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    elif current_user.is_group_leader:
        return redirect(url_for('group_leader_dashboard'))
    
    # Get recent test results
    recent_results = TestResult.query.filter_by(student_id=current_user.id)\
        .order_by(TestResult.date_taken.desc()).limit(5).all()
    
    # Get certificates
    certificates = Certificate.query.filter_by(student_id=current_user.id).all()
    
    # Get difficult topics
    difficult_topics = DifficultTopic.query.filter_by(student_id=current_user.id)\
        .join(Topic).all()
    
    # Get knowledge levels by subject
    knowledge_levels = KnowledgeLevel.query.filter_by(student_id=current_user.id)\
        .join(Subject).all()
    
    # Get group rating data if student has a group
    group_students = []
    if current_user.group_id:
        # Get students in this group (excluding group leaders)
        students = User.query.filter_by(group_id=current_user.group_id, is_group_leader=False).all()
        
        # Calculate statistics for each student
        for student in students:
            # Get test results for this student
            results = TestResult.query.filter_by(student_id=student.id).all()
            
            # Calculate statistics
            total_tests = len(results)
            total_questions = sum(r.total_questions for r in results)
            total_correct = sum(r.score for r in results)
            avg_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
            
            group_students.append({
                'student': student,
                'total_score': total_correct,
                'total_tests': total_tests,
                'avg_percentage': round(avg_percentage, 1)
            })
        
        # Sort by total score
        group_students.sort(key=lambda x: x['total_score'], reverse=True)
    
    return render_template('student_dashboard.html', 
                         user=current_user,
                         recent_results=recent_results,
                         certificates=certificates,
                         difficult_topics=difficult_topics,
                         knowledge_levels=knowledge_levels,
                         group_students=group_students)

@app.route('/group_leader/dashboard')
@app.route('/group_leader_dashboard')
@login_required
def group_leader_dashboard():
    if not current_user.is_group_leader:
        return redirect(url_for('student_dashboard'))
    
    # Check if group leader has a group
    if not current_user.group_id:
        flash('Siz hech qanday guruhga biriktirilmagansiz!', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # Get group students (excluding group leaders)
    group_students = User.query.filter_by(group_id=current_user.group_id, is_group_leader=False).all()
    
    # Get group test results
    group_results = []
    for student in group_students:
        results = TestResult.query.filter_by(student_id=student.id)\
            .order_by(TestResult.date_taken.desc()).limit(3).all()
        group_results.extend(results)
    
    # Get group statistics
    total_tests = len(group_results)
    total_questions = sum(r.total_questions for r in group_results)
    total_correct = sum(r.score for r in group_results)
    avg_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
    
    # Get group certificates
    group_certificates = Certificate.query.filter(
        Certificate.student_id.in_([s.id for s in group_students])
    ).all()
    
    # Get group ranking
    all_groups = Group.query.order_by(Group.total_score.desc()).all()
    group_rank = next((i+1 for i, g in enumerate(all_groups) if g.id == current_user.group_id), 0)
    
    return render_template('group_leader_dashboard.html', 
                         group=current_user.group,
                         group_students=group_students,
                         group_results=group_results[:10],
                         total_tests=total_tests,
                         avg_percentage=round(avg_percentage, 1),
                         group_certificates=group_certificates,
                         group_rank=group_rank,
                         total_groups=len(all_groups))

@app.route('/subjects')
@login_required
def subjects():
    all_subjects = Subject.query.all()
    return render_template('subjects.html', subjects=all_subjects)

@app.route('/subject/<int:subject_id>')
@login_required
def subject_detail(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    topics = Topic.query.filter_by(subject_id=subject_id).all()
    
    # Mark difficult topics for current student
    difficult_topic_ids = [dt.topic_id for dt in DifficultTopic.query.filter_by(student_id=current_user.id).all()]
    
    return render_template('subject_detail.html', 
                         subject=subject, 
                         topics=topics,
                         difficult_topic_ids=difficult_topic_ids)

@app.route('/mark_difficult/<int:topic_id>')
@login_required
def mark_difficult(topic_id):
    existing = DifficultTopic.query.filter_by(
        student_id=current_user.id, 
        topic_id=topic_id
    ).first()
    
    if existing:
        db.session.delete(existing)
        flash('Mavzu qiyinliklar ro\'yxatidan olib tashlandi!', 'success')
    else:
        difficult = DifficultTopic(student_id=current_user.id, topic_id=topic_id)
        db.session.add(difficult)
        flash('Mavzu qiyin deb belgilandi!', 'info')
    
    db.session.commit()
    return redirect(request.referrer)

@app.route('/upload_certificate', methods=['GET', 'POST'])
@login_required
def upload_certificate():
    if current_user.is_admin:
        flash('Adminlar sertifikat yuklay olmadi!', 'warning')
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('Fayl tanlanmagan!', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        title = request.form['title']
        description = request.form.get('description', '')
        
        if file.filename == '':
            flash('Fayl tanlanmagan!', 'danger')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(f"{current_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Create upload directory if it doesn't exist
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            file.save(file_path)
            
            certificate = Certificate(
                student_id=current_user.id,
                title=title,
                description=description,
                file_path=filename
            )
            
            db.session.add(certificate)
            
            # Award 10 points to student's group for certificate
            current_user.group.total_score += 10
            
            db.session.commit()
            
            flash(f'Sertifikat muvaffaqiyatli yuklandi! Guruhingizga 10 ball berildi!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Fayl formati noto\'g\'ri! Faqat PDF, DOC, DOCX, JPG, JPEG, PNG ruxsat etilgan.', 'danger')
    
    return render_template('upload_certificate.html')

@app.route('/tests')
@login_required
def tests():
    from datetime import timedelta
    current_time = datetime.utcnow()
    
    # Get available tests (not ended yet)
    available_tests = Test.query.filter(
        Test.test_date <= current_time,
        (Test.end_time.is_(None) | (Test.end_time > current_time))
    ).all()
    
    # Get results for current user
    user_results = {result.test_id: result for result in 
                   TestResult.query.filter_by(student_id=current_user.id).all()}
    
    # Prepare 7-day schedule data
    today = current_time.date()
    start_date = today
    week_schedule = []
    
    for i in range(7):
        test_date = start_date + timedelta(days=i)
        day_names = ["Dushanba", "Seshanba", "Chorshanba", "Payshanba", "Juma", "Shanba", "Yakshanba"]
        subjects = ["Huquq", "Ingliz tili", "DTM Test", "Tarix", "Ona tili", "DTM Test", "Matematika"]
        
        day_data = {
            'day_name': day_names[test_date.weekday()],
            'test_date': test_date,
            'subject_name': subjects[i],
            'is_dtm_day': i in [2, 5],
            'question_count': 90 if i in [2, 5] else 30,
            'duration': 120 if i in [2, 5] else 45,
            'test_time': "18:00" if i in [2, 5] else "08:00 - 22:00",
            'is_today': test_date == today,
            'is_past': test_date < today
        }
        week_schedule.append(day_data)
    
    return render_template('tests.html', 
                         tests=available_tests, 
                         user_results=user_results,
                         current_time=current_time,
                         week_schedule=week_schedule)

@app.route('/register_for_test/<int:test_id>', methods=['POST'])
@login_required
def register_for_test(test_id):
    test = Test.query.get_or_404(test_id)
    
    # Only allow registration for daily tests
    if not test.is_daily:
        flash('Faqat kundalik testlar uchun ro\'yxatdan o\'tish mumkin!', 'warning')
        return redirect(url_for('tests'))
    
    # Check if registration is still open (same day only)
    today = datetime.now().date()
    test_date = test.test_date.date()
    
    if test_date != today:
        flash('Faqat shu kunning testlari uchun ro\'yxatdan o\'tish mumkin!', 'warning')
        return redirect(url_for('tests'))
    
    # Check if already registered
    existing_registration = TestRegistration.query.filter_by(
        student_id=current_user.id,
        test_id=test_id
    ).first()
    
    if existing_registration:
        flash('Siz bu test uchun allaqachon ro\'yxatdan o\'tganmisiz!', 'warning')
        return redirect(url_for('tests'))
    
    # Create registration
    registration = TestRegistration(
        student_id=current_user.id,
        test_id=test_id
    )
    
    db.session.add(registration)
    db.session.commit()
    
    flash(f'{test.title} testi uchun muvaffaqiyatli ro\'yxatdan o\'tdingiz!', 'success')
    return redirect(url_for('tests'))

@app.route('/test/<int:test_id>')
@login_required
def take_test(test_id):
    test = Test.query.get_or_404(test_id)
    current_time = datetime.utcnow()
    
    # Check if test is available
    if test.test_date > current_time:
        flash('Test hali boshlanmagan!', 'warning')
        return redirect(url_for('tests'))
    
    # Time restrictions for different test types
    if test.is_daily:
        # Daily tests: available from 08:00 to 22:00 on test date
        test_date = test.test_date.date()
        current_date = current_time.date()
        current_hour = current_time.hour
        
        if current_date != test_date:
            flash('Faqat test kunida topshirish mumkin!', 'warning')
            return redirect(url_for('tests'))
        
        if current_hour < 8 or current_hour >= 22:
            flash('Kundalik testlar faqat soat 08:00 dan 22:00 gacha mavjud!', 'warning')
            return redirect(url_for('tests'))
            
    else:
        # DTM tests: available from 18:00, but late participants can join until 20:00
        test_date = test.test_date.date()
        current_date = current_time.date()
        current_hour = current_time.hour
        
        if current_date != test_date:
            flash('Faqat test kunida topshirish mumkin!', 'warning')
            return redirect(url_for('tests'))
        
        if current_hour < 18:
            flash('DTM testlar soat 18:00 dan boshlanadi!', 'warning')
            return redirect(url_for('tests'))
    
    if test.end_time and test.end_time <= current_time:
        flash('Test tugagan!', 'warning')
        return redirect(url_for('tests'))
    
    # Check if already taken
    existing_result = TestResult.query.filter_by(
        student_id=current_user.id, 
        test_id=test_id
    ).first()
    
    if existing_result:
        flash('Siz bu testni allaqachon topshirgansiz!', 'warning')
        return redirect(url_for('tests'))
    
    # Check if registered for this test
    registration = TestRegistration.query.filter_by(
        student_id=current_user.id,
        test_id=test_id
    ).first()
    
    if not registration:
        flash('Avval test uchun ro\'yxatdan o\'ting!', 'warning')
        return redirect(url_for('tests'))
    
    # Mark as attended
    registration.attended = True
    db.session.commit()
    
    questions = Question.query.filter_by(test_id=test_id).all()
    return render_template('take_test.html', test=test, questions=questions, current_time=current_time)

@app.route('/submit_test/<int:test_id>', methods=['POST'])
@login_required
def submit_test(test_id):
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test_id).all()
    
    score = 0
    for question in questions:
        user_answer = request.form.get(f'question_{question.id}')
        if user_answer == question.correct_answer:
            score += 1
    
    # Save result
    result = TestResult(
        student_id=current_user.id,
        test_id=test_id,
        score=score,
        total_questions=len(questions)
    )
    db.session.add(result)
    
    # Update knowledge level for this subject
    percentage = (score / len(questions)) * 100
    knowledge_level = KnowledgeLevel.query.filter_by(
        student_id=current_user.id,
        subject_id=test.subject_id
    ).first()
    
    if knowledge_level:
        # Update existing knowledge level (weighted average)
        old_weight = 0.7  # Give more weight to recent performance
        new_weight = 0.3
        knowledge_level.level = int(knowledge_level.level * old_weight + percentage * new_weight)
        knowledge_level.last_updated = datetime.utcnow()
    else:
        # Create new knowledge level
        knowledge_level = KnowledgeLevel(
            student_id=current_user.id,
            subject_id=test.subject_id,
            level=int(percentage)
        )
        db.session.add(knowledge_level)
    
    # Update group score if daily test
    if test.is_daily and score >= len(questions) * 0.8:  # 80% or higher
        current_user.group.total_score += score
        db.session.add(current_user.group)
    
    db.session.commit()
    
    flash(f'Test yakunlandi! Siz {score}/{len(questions)} ball to\'pladingiz!', 'success')
    return redirect(url_for('test_result', result_id=result.id))

@app.route('/edit_test/<int:test_id>', methods=['GET', 'POST'])
@login_required
def edit_test(test_id):
    if not current_user.is_admin:
        flash('Faqat administrator testlarni tahrirlashi mumkin!', 'danger')
        return redirect(url_for('tests'))
    
    test = Test.query.get_or_404(test_id)
    
    if request.method == 'POST':
        test.title = request.form.get('title')
        test.duration_minutes = int(request.form.get('duration_minutes', 60))
        
        if request.form.get('start_time'):
            test.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M')
        
        if request.form.get('end_time'):
            test.end_time = datetime.strptime(request.form.get('end_time'), '%H:%M')
        
        db.session.commit()
        flash('Test muvaffaqiyatli tahrirlandi!', 'success')
        return redirect(url_for('tests'))
    
    return render_template('edit_test.html', test=test)

@app.route('/delete_test/<int:test_id>', methods=['POST'])
@login_required
def delete_test(test_id):
    if not current_user.is_admin:
        flash('Faqat administrator testlarni o\'chirishi mumkin!', 'danger')
        return redirect(url_for('tests'))
    
    test = Test.query.get_or_404(test_id)
    
    # Delete related questions and results
    Question.query.filter_by(test_id=test_id).delete()
    TestResult.query.filter_by(test_id=test_id).delete()
    
    db.session.delete(test)
    db.session.commit()
    
    flash('Test muvaffaqiyatli o\'chirildi!', 'success')
    return redirect(url_for('tests'))

@app.route('/test_result/<int:result_id>')
@login_required
def test_result(result_id):
    result = TestResult.query.get_or_404(result_id)
    test = result.test
    current_time = datetime.utcnow()
    
    # Check if user owns this result or is admin/group leader
    if result.student_id != current_user.id and not current_user.is_admin and not current_user.is_group_leader:
        flash('Bu natijani ko\'rishga huquqingiz yo\'q!', 'danger')
        return redirect(url_for('student_dashboard'))
    
    # Check if results should be visible
    if test.is_daily:
        # Daily test results visible after 22:00 on test day
        test_date = test.test_date.date()
        current_date = current_time.date()
        current_hour = current_time.hour
        
        # Allow own result anytime, but others only after deadline
        if result.student_id != current_user.id:
            if current_date == test_date and current_hour < 22:
                flash('Boshqa o\'quvchilarning natijalari soat 22:00 dan keyin ko\'rinadi!', 'warning')
                return redirect(url_for('student_dashboard'))
            elif current_date < test_date:
                flash('Test hali tugamagan!', 'warning')
                return redirect(url_for('student_dashboard'))
    else:
        # DTM test results visible after test completion
        if result.student_id != current_user.id and test.test_date > current_time:
            flash('Test hali tugamagan!', 'warning')
            return redirect(url_for('student_dashboard'))
    
    # Get all registrations for this test
    registrations = TestRegistration.query.filter_by(test_id=test.id).all()
    
    # Get all results for this test, sorted by score
    all_results = TestResult.query.filter_by(test_id=test.id)\
        .join(User).order_by(TestResult.score.desc()).all()
    
    return render_template('test_result.html', result=result, registrations=registrations, all_results=all_results)

@app.route('/test_results/<int:test_id>')
@login_required
def test_results(test_id):
    test = Test.query.get_or_404(test_id)
    current_time = datetime.utcnow()
    
    # Check if results should be visible
    if test.is_daily:
        # Daily test results visible after 22:00 on test day
        test_date = test.test_date.date()
        current_date = current_time.date()
        current_hour = current_time.hour
        
        if current_date == test_date and current_hour < 22:
            flash('Kundalik test natijalari soat 22:00 dan keyin ko\'rinadi!', 'warning')
            return redirect(url_for('tests'))
        elif current_date < test_date:
            flash('Test hali tugamagan!', 'warning')
            return redirect(url_for('tests'))
    else:
        # DTM test results visible after test completion
        if test.test_date > current_time:
            flash('Test hali tugamagan!', 'warning')
            return redirect(url_for('tests'))
    
    # Get all results for this test, sorted by score
    all_results = TestResult.query.filter_by(test_id=test_id)\
        .join(User).order_by(TestResult.score.desc()).all()
    
    return render_template('test_results.html', test=test, results=all_results)

@app.route('/schedule')
@login_required
def schedule():
    if current_user.is_admin:
        schedules = Schedule.query.all()
    else:
        schedules = Schedule.query.filter_by(group_id=current_user.group_id).all()
    
    # Organize by day of week
    schedule_by_day = {}
    days = ['Dushanba', 'Seshanba', 'Chorshanba', 'Payshanba', 'Juma', 'Shanba', 'Yakshanba']
    
    for day_num in range(7):
        schedule_by_day[days[day_num]] = [
            schedule for schedule in schedules 
            if schedule.day_of_week == day_num
        ]
    
    return render_template('schedule.html', schedule_by_day=schedule_by_day)

@app.route('/groups_rating')
@login_required
def groups_rating():
    groups = Group.query.order_by(Group.total_score.desc()).all()
    
    # Calculate detailed statistics for each group
    group_stats = []
    for group in groups:
        # Get students in this group (excluding group leaders)
        students = User.query.filter_by(group_id=group.id, is_group_leader=False).all()
        
        # Get test results for this group
        group_results = []
        for student in students:
            results = TestResult.query.filter_by(student_id=student.id).all()
            group_results.extend(results)
        
        # Calculate statistics
        total_tests = len(group_results)
        total_questions = sum(r.total_questions for r in group_results)
        total_correct = sum(r.score for r in group_results)
        avg_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        # Get certificate count
        certificate_count = Certificate.query.filter(Certificate.student_id.in_([s.id for s in students])).count()
        
        # Get top 3 students
        student_scores = {}
        for student in students:
            student_scores[student.id] = sum(r.score for r in TestResult.query.filter_by(student_id=student.id).all())
        
        top_students = sorted(students, key=lambda s: student_scores.get(s.id, 0), reverse=True)[:3]
        
        group_stats.append({
            'group': group,
            'student_count': len(students),
            'total_tests': total_tests,
            'avg_percentage': round(avg_percentage, 1),
            'certificate_count': certificate_count,
            'top_students': top_students,
            'total_score': group.total_score
        })
    
    return render_template('groups_rating.html', group_stats=group_stats)

@app.route('/group_rating/<int:group_id>')
@login_required
def group_rating(group_id):
    # Check if user can access this group rating
    if current_user.is_admin:
        # Admin can see any group
        group = Group.query.get_or_404(group_id)
    elif current_user.is_group_leader:
        # Group leader can only see their own group
        if current_user.group_id != group_id:
            flash('Bu guruh reytingini ko\'rishga huquqingiz yo\'q!', 'danger')
            return redirect(url_for('student_dashboard'))
        group = Group.query.get_or_404(group_id)
    else:
        # Regular students can only see their own group rating
        if current_user.group_id != group_id:
            flash('Bu guruh reytingini ko\'rishga huquqingiz yo\'q!', 'danger')
            return redirect(url_for('student_dashboard'))
        group = Group.query.get_or_404(group_id)
    
    # Get students in this group (excluding group leaders)
    students = User.query.filter_by(group_id=group_id, is_group_leader=False).all()
    
    # Calculate detailed statistics for each student
    student_stats = []
    for student in students:
        # Get test results for this student
        results = TestResult.query.filter_by(student_id=student.id).all()
        
        # Calculate statistics
        total_tests = len(results)
        total_questions = sum(r.total_questions for r in results)
        total_correct = sum(r.score for r in results)
        avg_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        # Get certificate count
        certificate_count = Certificate.query.filter_by(student_id=student.id).count()
        
        # Get recent results
        recent_results = TestResult.query.filter_by(student_id=student.id)\
            .order_by(TestResult.date_taken.desc()).limit(5).all()
        
        student_stats.append({
            'student': student,
            'total_score': total_correct,
            'total_tests': total_tests,
            'avg_percentage': round(avg_percentage, 1),
            'certificate_count': certificate_count,
            'recent_results': recent_results
        })
    
    # Sort by total score
    student_stats.sort(key=lambda x: x['total_score'], reverse=True)
    
    return render_template('group_rating.html', group=group, student_stats=student_stats)

# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    total_students = User.query.filter_by(is_admin=False).count()
    total_groups = Group.query.count()
    total_tests = Test.query.count()
    recent_results = TestResult.query.order_by(TestResult.date_taken.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html',
                         total_students=total_students,
                         total_groups=total_groups,
                         total_tests=total_tests,
                         recent_results=recent_results)

@app.route('/admin/students')
@login_required
def admin_students():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    students = User.query.filter_by(is_admin=False).all()
    groups = Group.query.all()
    return render_template('admin_students.html', students=students, groups=groups)

@app.route('/admin/subjects')
@login_required
def admin_subjects():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    subjects = Subject.query.all()
    return render_template('admin_subjects.html', subjects=subjects)

@app.route('/admin/add_student', methods=['POST'])
@login_required
def admin_add_student():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    username = request.form['username']
    password = request.form['password']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    group_id = request.form['group_id']
    
    # Check if username already exists
    if User.query.filter_by(username=username).first():
        flash('Bu login allaqachon mavjud!', 'danger')
        return redirect(url_for('admin_students'))
    
    # Create new student
    student = User(
        username=username,
        password_hash=generate_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        group_id=group_id,
        is_admin=False
    )
    
    db.session.add(student)
    db.session.commit()
    
    flash('O\'quvchi muvaffaqiyatli qo\'shildi!', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/reset_password/<int:student_id>', methods=['POST'])
@login_required
def admin_reset_password(student_id):
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    student = User.query.get_or_404(student_id)
    new_password = request.form['new_password']
    
    student.password_hash = generate_password_hash(new_password)
    db.session.commit()
    
    flash(f'{student.first_name} {student.last_name} paroli muvaffaqiyatli yangilandi!', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/delete_student/<int:student_id>', methods=['POST'])
@login_required
def admin_delete_student(student_id):
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    student = User.query.get_or_404(student_id)
    
    # Delete related records
    TestResult.query.filter_by(student_id=student_id).delete()
    Certificate.query.filter_by(student_id=student_id).delete()
    DifficultTopic.query.filter_by(student_id=student_id).delete()
    KnowledgeLevel.query.filter_by(student_id=student_id).delete()
    TestRegistration.query.filter_by(student_id=student_id).delete()
    
    # Delete student
    db.session.delete(student)
    db.session.commit()
    
    flash('O\'quvchi muvaffaqiyatli o\'chirildi!', 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/add_group_leader', methods=['POST'])
@login_required
def admin_add_group_leader():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    username = request.form['username']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    group_id = request.form['group_id']
    
    # Check if username exists
    if User.query.filter_by(username=username).first():
        flash('Bu username allaqachon mavjud!', 'danger')
        return redirect(url_for('admin_groups'))
    
    # Generate one-time password
    import random
    import string
    one_time_password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    group_leader = User(
        username=username,
        password_hash=generate_password_hash(one_time_password),
        first_name=first_name,
        last_name=last_name,
        group_id=group_id,
        is_group_leader=True,
        needs_password_change=True
    )
    
    db.session.add(group_leader)
    db.session.commit()
    
    flash(f'Guruh rahbari muvaffaqiyatli qo\'shildi! Bir martalik parol: {one_time_password}', 'success')
    return redirect(url_for('admin_groups'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if not current_user.needs_password_change:
        flash('Parolni o\'zgartirishga hojat yo\'q!', 'warning')
        return redirect(url_for('student_dashboard'))
    
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('Parollar mos kelmadi!', 'danger')
            return render_template('change_password.html')
        
        current_user.password_hash = generate_password_hash(new_password)
        current_user.needs_password_change = False
        db.session.commit()
        
        flash('Parol muvaffaqiyatli o\'zgartirildi!', 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('change_password.html')


@app.route('/admin/groups')
@login_required
def admin_groups():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    groups = Group.query.all()
    return render_template('admin_groups.html', groups=groups)

@app.route('/admin/add_group', methods=['POST'])
@login_required
def admin_add_group():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    name = request.form['name']
    group = Group(name=name)
    
    db.session.add(group)
    db.session.commit()
    
    flash('Guruh muvaffaqiyatli qo\'shildi!', 'success')
    return redirect(url_for('admin_groups'))

@app.route('/admin/edit_group/<int:group_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_group(group_id):
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    group = Group.query.get_or_404(group_id)
    
    if request.method == 'POST':
        group.name = request.form['name']
        db.session.commit()
        flash('Guruh muvaffaqiyatli tahrirlandi!', 'success')
        return redirect(url_for('admin_groups'))
    
    return render_template('edit_group.html', group=group)

@app.route('/admin/delete_group/<int:group_id>', methods=['POST'])
@login_required
def admin_delete_group(group_id):
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    group = Group.query.get_or_404(group_id)
    
    # Check if group has students
    students = User.query.filter_by(group_id=group_id).all()
    if students:
        flash('Guruhda o\'quvchilar mavjud, o\'chirib bo\'lmaydi!', 'danger')
        return redirect(url_for('admin_groups'))
    
    db.session.delete(group)
    db.session.commit()
    flash('Guruh muvaffaqiyatli o\'chirildi!', 'success')
    return redirect(url_for('admin_groups'))

@app.route('/admin/schedule')
@login_required
def admin_schedule():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    schedules = Schedule.query.all()
    groups = Group.query.all()
    subjects = Subject.query.all()
    return render_template('admin_schedule.html', schedules=schedules, groups=groups, subjects=subjects)

@app.route('/admin/add_schedule', methods=['POST'])
@login_required
def admin_add_schedule():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    group_id = request.form['group_id']
    subject_id = request.form['subject_id']
    day_of_week = request.form['day_of_week']
    time_slot = request.form['time_slot']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    
    schedule = Schedule(
        group_id=group_id,
        subject_id=subject_id,
        day_of_week=int(day_of_week),
        time_slot=time_slot,
        start_time=datetime.strptime(start_time, '%H:%M').time() if start_time else None,
        end_time=datetime.strptime(end_time, '%H:%M').time() if end_time else None
    )
    
    db.session.add(schedule)
    db.session.commit()
    
    flash('Dars jadvali muvaffaqiyatli qo\'shildi!', 'success')
    return redirect(url_for('admin_schedule'))

@app.route('/admin/edit_schedule/<int:schedule_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_schedule(schedule_id):
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    schedule = Schedule.query.get_or_404(schedule_id)
    
    if request.method == 'POST':
        schedule.group_id = request.form['group_id']
        schedule.subject_id = request.form['subject_id']
        schedule.day_of_week = int(request.form['day_of_week'])
        schedule.time_slot = request.form['time_slot']
        
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        schedule.start_time = datetime.strptime(start_time, '%H:%M').time() if start_time else None
        schedule.end_time = datetime.strptime(end_time, '%H:%M').time() if end_time else None
        
        db.session.commit()
        
        flash('Dars jadvali muvaffaqiyatli yangilandi!', 'success')
        return redirect(url_for('admin_schedule'))
    
    groups = Group.query.all()
    subjects = Subject.query.all()
    
    return render_template('edit_schedule.html', schedule=schedule, groups=groups, subjects=subjects)

@app.route('/admin/delete_schedule/<int:schedule_id>', methods=['POST'])
@login_required
def admin_delete_schedule(schedule_id):
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    
    flash('Dars jadvali muvaffaqiyatli o\'chirildi!', 'success')
    return redirect(url_for('admin_schedule'))

@app.route('/admin/add_subject', methods=['POST'])
@login_required
def admin_add_subject():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    name = request.form['name']
    description = request.form.get('description', '')
    
    subject = Subject(name=name, description=description)
    db.session.add(subject)
    db.session.commit()
    
    flash('Fan muvaffaqiyatli qo\'shildi!', 'success')
    return redirect(url_for('admin_subjects'))

@app.route('/admin/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_subject(subject_id):
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'POST':
        subject.name = request.form.get('name')
        subject.description = request.form.get('description', '')
        
        db.session.commit()
        flash('Fan muvaffaqiyatli tahrirlandi!', 'success')
        return redirect(url_for('admin_subjects'))
    
    return render_template('edit_subject.html', subject=subject)

@app.route('/admin/delete_subject/<int:subject_id>', methods=['POST'])
@login_required
def admin_delete_subject(subject_id):
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    subject = Subject.query.get_or_404(subject_id)
    
    # Check if subject has related tests
    related_tests = Test.query.filter_by(subject_id=subject_id).count()
    if related_tests > 0:
        flash(f'Ushbu fanga {related_tests} ta test bog\'langan! Avval testlarni o\'chirishingiz kerak.', 'danger')
        return redirect(url_for('admin_subjects'))
    
    # Delete related topics
    Topic.query.filter_by(subject_id=subject_id).delete()
    
    db.session.delete(subject)
    db.session.commit()
    
    flash('Fan muvaffaqiyatli o\'chirildi!', 'success')
    return redirect(url_for('admin_subjects'))

@app.route('/admin/add_topic', methods=['POST'])
@login_required
def admin_add_topic():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    title = request.form['title']
    content = request.form['content']
    video_url = request.form.get('video_url', '')
    subject_id = request.form['subject_id']
    
    topic = Topic(
        title=title,
        content=content,
        video_url=video_url,
        subject_id=subject_id
    )
    
    db.session.add(topic)
    db.session.commit()
    
    flash('Mavzu muvaffaqiyatli qo\'shildi!', 'success')
    return redirect(url_for('admin_subjects'))

@app.route('/admin/tests')
@login_required
def admin_tests():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    tests = Test.query.all()
    subjects = Subject.query.all()
    return render_template('admin_tests.html', tests=tests, subjects=subjects)

@app.route('/admin/add_test', methods=['POST'])
@login_required
def admin_add_test():
    if not current_user.is_admin:
        return redirect(url_for('student_dashboard'))
    
    title = request.form['title']
    subject_id = request.form['subject_id']
    is_daily = 'is_daily' in request.form
    is_comprehensive = 'is_comprehensive' in request.form
    is_dtm = 'is_dtm' in request.form
    duration_minutes = int(request.form.get('duration_minutes', 60))
    
    # Parse dates
    test_date_str = request.form['test_date']
    test_date = datetime.strptime(test_date_str, '%Y-%m-%d')
    
    # Parse optional times
    start_time = None
    end_time = None
    
    if request.form.get('start_time'):
        start_time_str = request.form['start_time']
        start_time = datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
    
    if request.form.get('end_time'):
        end_time_str = request.form['end_time']
        end_time = datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
    
    test = Test(
        title=title,
        subject_id=subject_id,
        is_daily=is_daily,
        is_comprehensive=is_comprehensive,
        is_dtm=is_dtm,
        duration_minutes=duration_minutes,
        test_date=test_date,
        start_time=start_time,
        end_time=end_time
    )
    
    db.session.add(test)
    db.session.commit()
    
    flash('Test muvaffaqiyatli qo\'shildi!', 'success')
    return redirect(url_for('admin_tests'))



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        admin = User.query.filter_by(username='AkmalJaxonkulov').first()
        if not admin:
            admin = User(
                username='AkmalJaxonkulov',
                password_hash=generate_password_hash('Akmal1221'),
                first_name='Akmal',
                last_name='Jaxonkulov',
                group_id=1,  # Will be created below
                is_admin=True
            )
            db.session.add(admin)
        
        # Create predefined groups 101-108 if not exists
        for i in range(101, 109):
            group_name = str(i)
            group = Group.query.filter_by(name=group_name).first()
            if not group:
                group = Group(name=group_name)
                db.session.add(group)
        
        # Create default group if not exists (fallback)
        default_group = Group.query.filter_by(name='Default Group').first()
        if not default_group:
            default_group = Group(name='Default Group')
            db.session.add(default_group)
        
        db.session.flush()  # Get the IDs
        
        # Update admin's group_id to first available group
        first_group = Group.query.first()
        if admin.group_id == 1 and first_group and first_group.id != 1:
            admin.group_id = first_group.id
        
        db.session.commit()
    
    app.run(debug=True)
