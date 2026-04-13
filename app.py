import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-sessions-to-work'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///education.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_group_leader = db.Column(db.Boolean, default=False)
    needs_password_change = db.Column(db.Boolean, default=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'))
    
    # Relationships
    group = db.relationship('Group', backref=db.backref('students', lazy=True))

class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    total_score = db.Column(db.Integer, default=0)

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    video_url = db.Column(db.String(500))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    
    subject = db.relationship('Subject', backref=db.backref('topics', lazy=True))

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

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(500), nullable=False)
    option_b = db.Column(db.String(500), nullable=False)
    option_c = db.Column(db.String(500), nullable=False)
    option_d = db.Column(db.String(500), nullable=False)
    correct_answer = db.Column(db.String(1), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    
    test = db.relationship('Test', backref=db.backref('questions', lazy=True))

class TestResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    total_questions = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    test_id = db.Column(db.Integer, db.ForeignKey('test.id'), nullable=False)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('test_results', lazy=True))
    test = db.relationship('Test', backref=db.backref('results', lazy=True))

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    
    group = db.relationship('Group', backref=db.backref('schedules', lazy=True))

class Certificate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('certificates', lazy=True))

class DifficultTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('difficult_topics', lazy=True))
    topic = db.relationship('Topic', backref=db.backref('marked_by', lazy=True))

# Decorators
def login_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in', False):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin', False):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    # Create a simple current_user object for templates
    class CurrentUser:
        def __init__(self):
            self.is_authenticated = session.get('logged_in', False)
            self.is_admin = session.get('is_admin', False)
            self.username = session.get('username', '')
            self.id = session.get('user_id', None)
        
        def is_authenticated(self):
            return self.is_authenticated
    
    return dict(current_user=CurrentUser())

# Routes

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        print(f"Login attempt: username='{username}', password_length={len(password)}")
        
        if username == 'AkmalJaxonkulov' and password == 'Akmal1221':
            print("Admin credentials correct!")
            # Create admin user if not exists
            admin_user = User.query.filter_by(username='AkmalJaxonkulov').first()
            if not admin_user:
                default_group = Group.query.filter_by(id=1).first()
                if not default_group:
                    default_group = Group(id=1, name='Default', total_score=0)
                    db.session.add(default_group)
                    db.session.flush()
                
                admin_user = User(
                    username='AkmalJaxonkulov',
                    password_hash=generate_password_hash('Akmal1221'),
                    first_name='Akmal',
                    last_name='Jaxonkulov',
                    group_id=1,
                    is_admin=True
                )
                db.session.add(admin_user)
                db.session.commit()
            
            # Store in session
            session.clear()
            session['user_id'] = admin_user.id
            session['username'] = admin_user.username
            session['is_admin'] = admin_user.is_admin
            session['logged_in'] = True
            session.permanent = True
            
            print(f"Session created: {dict(session)}")
            print("Redirecting to admin dashboard...")
            
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('login.html', error="Login yoki parol noto'g'ri!")
    
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    print(f"Admin dashboard accessed. Session: {dict(session)}")
    
    # Check if user is logged in
    if not session.get('logged_in', False):
        print("Not logged in, redirecting to login")
        return redirect(url_for('login'))
    
    if not session.get('is_admin', False):
        print("Not admin, redirecting to login")
        return redirect(url_for('login'))
    total_students = User.query.filter_by(is_admin=False).count()
    total_groups = Group.query.count()
    total_tests = Test.query.count()
    total_subjects = Subject.query.count()
    
    recent_results = TestResult.query.order_by(TestResult.taken_at.desc()).limit(5).all()
    
    return render_template('admin_dashboard.html',
                         total_students=total_students,
                         total_groups=total_groups,
                         total_tests=total_tests,
                         total_subjects=total_subjects,
                         recent_results=recent_results)

@app.route('/admin/students')
def admin_students():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    students = User.query.filter_by(is_admin=False).all()
    groups = Group.query.all()
    return render_template('admin_students.html', students=students, groups=groups)

@app.route('/admin/add_student', methods=['POST'])
def admin_add_student():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    group_id = request.form.get('group_id', type=int)
    
    # Check if username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash("Bu login allaqachon mavjud!", 'error')
        return redirect(url_for('admin_students'))
    
    # Create new student
    new_student = User(
        username=username,
        password_hash=generate_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        group_id=group_id,
        is_admin=False
    )
    db.session.add(new_student)
    db.session.commit()
    
    flash("O'quvchi muvaffaqiyatli qo'shildi!", 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/edit_student/<int:student_id>', methods=['GET', 'POST'])
def admin_edit_student(student_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    student = User.query.get_or_404(student_id)
    groups = Group.query.all()
    
    if request.method == 'POST':
        student.first_name = request.form.get('first_name', '').strip()
        student.last_name = request.form.get('last_name', '').strip()
        student.group_id = request.form.get('group_id', type=int)
        
        if request.form.get('password'):
            student.password_hash = generate_password_hash(request.form.get('password'))
        
        db.session.commit()
        flash("O'quvchi ma'lumotlari yangilandi!", 'success')
        return redirect(url_for('admin_students'))
    
    return render_template('edit_student.html', student=student, groups=groups)

@app.route('/admin/delete_student/<int:student_id>')
def admin_delete_student(student_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    student = User.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    
    flash("O'quvchi o'chirildi!", 'success')
    return redirect(url_for('admin_students'))

@app.route('/admin/groups')
def admin_groups():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    groups = Group.query.all()
    return render_template('admin_groups.html', groups=groups)

@app.route('/admin/add_group', methods=['POST'])
def admin_add_group():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    name = request.form.get('name', '').strip()
    
    # Check if group already exists
    existing_group = Group.query.filter_by(name=name).first()
    if existing_group:
        flash("Bu guruh nomi allaqachon mavjud!", 'error')
        return redirect(url_for('admin_groups'))
    
    # Create new group
    new_group = Group(name=name, total_score=0)
    db.session.add(new_group)
    db.session.commit()
    
    flash("Guruh muvaffaqiyatli qo'shildi!", 'success')
    return redirect(url_for('admin_groups'))

@app.route('/admin/edit_group/<int:group_id>', methods=['GET', 'POST'])
def admin_edit_group(group_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    group = Group.query.get_or_404(group_id)
    
    if request.method == 'POST':
        group.name = request.form.get('name', '').strip()
        db.session.commit()
        flash("Guruh ma'lumotlari yangilandi!", 'success')
        return redirect(url_for('admin_groups'))
    
    return render_template('edit_group.html', group=group)

@app.route('/admin/delete_group/<int:group_id>')
def admin_delete_group(group_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    group = Group.query.get_or_404(group_id)
    
    # Check if group has students
    if group.students:
        flash("Bu guruhda o'quvchilar bor, avval ularni o'chirishingiz kerak!", 'error')
        return redirect(url_for('admin_groups'))
    
    db.session.delete(group)
    db.session.commit()
    
    flash("Guruh o'chirildi!", 'success')
    return redirect(url_for('admin_groups'))

@app.route('/admin/subjects')
def admin_subjects():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    subjects = Subject.query.all()
    return render_template('admin_subjects.html', subjects=subjects)

@app.route('/admin/add_subject', methods=['POST'])
def admin_add_subject():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    
    # Create new subject
    new_subject = Subject(name=name, description=description)
    db.session.add(new_subject)
    db.session.commit()
    
    flash("Fan muvaffaqiyatli qo'shildi!", 'success')
    return redirect(url_for('admin_subjects'))

@app.route('/admin/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
def admin_edit_subject(subject_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    subject = Subject.query.get_or_404(subject_id)
    
    if request.method == 'POST':
        subject.name = request.form.get('name', '').strip()
        subject.description = request.form.get('description', '').strip()
        db.session.commit()
        flash("Fan ma'lumotlari yangilandi!", 'success')
        return redirect(url_for('admin_subjects'))
    
    return render_template('edit_subject.html', subject=subject)

@app.route('/admin/delete_subject/<int:subject_id>')
def admin_delete_subject(subject_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    subject = Subject.query.get_or_404(subject_id)
    
    # Check if subject has topics or tests
    if subject.topics or subject.tests:
        flash("Bu fan mavzular yoki testlarga ega, avval ularni o'chirishingiz kerak!", 'error')
        return redirect(url_for('admin_subjects'))
    
    db.session.delete(subject)
    db.session.commit()
    
    flash("Fan o'chirildi!", 'success')
    return redirect(url_for('admin_subjects'))

@app.route('/admin/add_topic', methods=['POST'])
def admin_add_topic():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    video_url = request.form.get('video_url', '').strip()
    subject_id = request.form.get('subject_id', type=int)
    
    # Create new topic
    new_topic = Topic(
        title=title,
        content=content,
        video_url=video_url,
        subject_id=subject_id
    )
    db.session.add(new_topic)
    db.session.commit()
    
    flash("Mavzu muvaffaqiyatli qo'shildi!", 'success')
    return redirect(url_for('admin_subjects'))

@app.route('/admin/topics')
def admin_topics():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    topics = Topic.query.all()
    subjects = Subject.query.all()
    return render_template('admin_topics.html', topics=topics, subjects=subjects)

@app.route('/admin/edit_topic/<int:topic_id>', methods=['GET', 'POST'])
def admin_edit_topic(topic_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    topic = Topic.query.get_or_404(topic_id)
    subjects = Subject.query.all()
    
    if request.method == 'POST':
        topic.title = request.form.get('title', '').strip()
        topic.content = request.form.get('content', '').strip()
        topic.video_url = request.form.get('video_url', '').strip()
        topic.subject_id = request.form.get('subject_id', type=int)
        
        db.session.commit()
        flash("Mavzu ma'lumotlari yangilandi!", 'success')
        return redirect(url_for('admin_topics'))
    
    return render_template('edit_topic.html', topic=topic, subjects=subjects)

@app.route('/admin/delete_topic/<int:topic_id>')
def admin_delete_topic(topic_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    topic = Topic.query.get_or_404(topic_id)
    
    # Check if topic is marked as difficult by any user
    if topic.marked_by:
        flash("Bu mavzu ba'zi o'quvchilar tomonidan qiyin deb belgilangan!", 'error')
        return redirect(url_for('admin_topics'))
    
    db.session.delete(topic)
    db.session.commit()
    
    flash("Mavzu o'chirildi!", 'success')
    return redirect(url_for('admin_topics'))

@app.route('/admin/tests')
def admin_tests():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    tests = Test.query.all()
    subjects = Subject.query.all()
    return render_template('admin_tests.html', tests=tests, subjects=subjects)

@app.route('/admin/add_test', methods=['POST'])
def admin_add_test():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    title = request.form.get('title', '').strip()
    subject_id = request.form.get('subject_id', type=int)
    is_daily = 'is_daily' in request.form
    is_comprehensive = 'is_comprehensive' in request.form
    is_dtm = 'is_dtm' in request.form
    duration_minutes = request.form.get('duration_minutes', type=int, default=60)
    
    # Create new test
    new_test = Test(
        title=title,
        subject_id=subject_id,
        is_daily=is_daily,
        is_comprehensive=is_comprehensive,
        is_dtm=is_dtm,
        duration_minutes=duration_minutes
    )
    db.session.add(new_test)
    db.session.commit()
    
    flash("Test muvaffaqiyatli qo'shildi!", 'success')
    return redirect(url_for('admin_tests'))

@app.route('/admin/edit_test/<int:test_id>', methods=['GET', 'POST'])
def admin_edit_test(test_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    test = Test.query.get_or_404(test_id)
    subjects = Subject.query.all()
    
    if request.method == 'POST':
        test.title = request.form.get('title', '').strip()
        test.subject_id = request.form.get('subject_id', type=int)
        test.is_daily = 'is_daily' in request.form
        test.is_comprehensive = 'is_comprehensive' in request.form
        test.is_dtm = 'is_dtm' in request.form
        test.duration_minutes = request.form.get('duration_minutes', type=int, default=60)
        
        db.session.commit()
        flash("Test ma'lumotlari yangilandi!", 'success')
        return redirect(url_for('admin_tests'))
    
    return render_template('edit_test.html', test=test, subjects=subjects)

@app.route('/admin/delete_test/<int:test_id>')
def admin_delete_test(test_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    test = Test.query.get_or_404(test_id)
    
    # Check if test has results
    if test.results:
        flash("Bu test natijalarga ega, avval ularni o'chirishingiz kerak!", 'error')
        return redirect(url_for('admin_tests'))
    
    db.session.delete(test)
    db.session.commit()
    
    flash("Test o'chirildi!", 'success')
    return redirect(url_for('admin_tests'))

@app.route('/admin/test_questions/<int:test_id>')
def admin_test_questions(test_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test_id).all()
    
    return render_template('admin_test_questions.html', test=test, questions=questions)

@app.route('/admin/add_question/<int:test_id>', methods=['POST'])
def admin_add_question(test_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    text = request.form.get('text', '').strip()
    option_a = request.form.get('option_a', '').strip()
    option_b = request.form.get('option_b', '').strip()
    option_c = request.form.get('option_c', '').strip()
    option_d = request.form.get('option_d', '').strip()
    correct_answer = request.form.get('correct_answer', '').strip().upper()
    
    # Create new question
    new_question = Question(
        text=text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_answer=correct_answer,
        test_id=test_id
    )
    db.session.add(new_question)
    db.session.commit()
    
    flash("Savol muvaffaqiyatli qo'shildi!", 'success')
    return redirect(url_for('admin_test_questions', test_id=test_id))

@app.route('/admin/test_results/<int:test_id>')
def admin_test_results(test_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    test = Test.query.get_or_404(test_id)
    results = TestResult.query.filter_by(test_id=test_id).order_by(TestResult.taken_at.desc()).all()
    
    # Calculate statistics
    total_attempts = len(results)
    avg_score = 0
    pass_count = 0
    
    if total_attempts > 0:
        total_score = sum(r.score for r in results)
        avg_score = total_score / total_attempts
        pass_count = len([r for r in results if r.score >= r.total_questions * 0.6])  # 60% passing
    
    return render_template('admin_test_results.html', 
                         test=test, 
                         results=results, 
                         total_attempts=total_attempts,
                         avg_score=avg_score,
                         pass_count=pass_count)

@app.route('/admin/schedule')
def admin_schedule():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    schedules = Schedule.query.all()
    groups = Group.query.all()
    return render_template('admin_schedule.html', schedules=schedules, groups=groups)

@app.route('/admin/add_schedule', methods=['POST'])
def admin_add_schedule():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    title = request.form.get('title', '').strip()
    subject_name = request.form.get('subject_name', '').strip()
    date_str = request.form.get('date', '').strip()
    start_time_str = request.form.get('start_time', '').strip()
    end_time_str = request.form.get('end_time', '').strip()
    group_id = request.form.get('group_id', type=int)
    
    # Parse date and time
    date = datetime.strptime(date_str, '%Y-%m-%d').date()
    start_time = datetime.strptime(start_time_str, '%H:%M').time()
    end_time = datetime.strptime(end_time_str, '%H:%M').time()
    
    # Create new schedule
    new_schedule = Schedule(
        title=title,
        subject_name=subject_name,
        date=date,
        start_time=start_time,
        end_time=end_time,
        group_id=group_id
    )
    db.session.add(new_schedule)
    db.session.commit()
    
    flash("Dars jadvali muvaffaqiyatli qo'shildi!", 'success')
    return redirect(url_for('admin_schedule'))

@app.route('/admin/edit_schedule/<int:schedule_id>', methods=['GET', 'POST'])
def admin_edit_schedule(schedule_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    schedule = Schedule.query.get_or_404(schedule_id)
    groups = Group.query.all()
    
    if request.method == 'POST':
        schedule.title = request.form.get('title', '').strip()
        schedule.subject_name = request.form.get('subject_name', '').strip()
        
        date_str = request.form.get('date', '').strip()
        start_time_str = request.form.get('start_time', '').strip()
        end_time_str = request.form.get('end_time', '').strip()
        group_id = request.form.get('group_id', type=int)
        
        schedule.date = datetime.strptime(date_str, '%Y-%m-%d').date()
        schedule.start_time = datetime.strptime(start_time_str, '%H:%M').time()
        schedule.end_time = datetime.strptime(end_time_str, '%H:%M').time()
        schedule.group_id = group_id
        
        db.session.commit()
        flash("Dars jadvali ma'lumotlari yangilandi!", 'success')
        return redirect(url_for('admin_schedule'))
    
    return render_template('edit_schedule.html', schedule=schedule, groups=groups)

@app.route('/admin/delete_schedule/<int:schedule_id>')
def admin_delete_schedule(schedule_id):
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    
    schedule = Schedule.query.get_or_404(schedule_id)
    db.session.delete(schedule)
    db.session.commit()
    
    flash("Dars jadvali o'chirildi!", 'success')
    return redirect(url_for('admin_schedule'))

@app.route('/student/dashboard')
def student_dashboard():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    recent_results = TestResult.query.filter_by(user_id=user.id).order_by(TestResult.taken_at.desc()).limit(5).all()
    certificates = Certificate.query.filter_by(user_id=user.id).all()
    difficult_topics = DifficultTopic.query.filter_by(user_id=user.id).count()
    
    return render_template('student_dashboard.html',
                         user=user,
                         recent_results=recent_results,
                         certificates=certificates,
                         difficult_topics=difficult_topics)

@app.route('/group_leader/dashboard')
def group_leader_dashboard():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    
    if not user.is_group_leader:
        return redirect(url_for('student_dashboard'))
    
    # Get group members
    group_members = User.query.filter_by(group_id=user.group_id, is_admin=False).all()
    
    # Get group statistics
    total_members = len(group_members)
    avg_score = 0
    if total_members > 0:
        total_score = sum([g.id for g in group_members])  # Placeholder for actual scoring
        avg_score = user.group.total_score / total_members if total_members > 0 else 0
    
    # Get recent test results for group
    group_student_ids = [s.id for s in group_members]
    recent_group_results = TestResult.query.filter(TestResult.user_id.in_(group_student_ids)).order_by(TestResult.taken_at.desc()).limit(10).all()
    
    return render_template('group_leader_dashboard.html',
                         user=user,
                         group_members=group_members,
                         total_members=total_members,
                         avg_score=avg_score,
                         recent_group_results=recent_group_results)

@app.route('/subjects')
def subjects():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    subjects = Subject.query.all()
    return render_template('subjects.html', subjects=subjects)

@app.route('/subject/<int:subject_id>')
def subject_detail(subject_id):
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    subject = Subject.query.get_or_404(subject_id)
    topics = Topic.query.filter_by(subject_id=subject_id).all()
    user = User.query.get(session['user_id'])
    
    # Get difficult topics for this user
    difficult_topic_ids = [dt.topic_id for dt in DifficultTopic.query.filter_by(user_id=user.id).all()]
    
    return render_template('subject_detail.html',
                         subject=subject,
                         topics=topics,
                         difficult_topic_ids=difficult_topic_ids)

@app.route('/tests')
def tests():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    tests = Test.query.all()
    user_results = {result.test_id: result for result in TestResult.query.filter_by(user_id=session['user_id']).all()}
    
    return render_template('tests.html', tests=tests, user_results=user_results)

@app.route('/take_test/<int:test_id>')
def take_test(test_id):
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test_id).all()
    
    return render_template('take_test.html', test=test, questions=questions)

@app.route('/submit_test/<int:test_id>', methods=['POST'])
def submit_test(test_id):
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    test = Test.query.get_or_404(test_id)
    questions = Question.query.filter_by(test_id=test_id).all()
    
    score = 0
    for question in questions:
        user_answer = request.form.get(f'question_{question.id}')
        if user_answer == question.correct_answer:
            score += 1
    
    # Save result
    result = TestResult(
        score=score,
        total_questions=len(questions),
        user_id=session['user_id'],
        test_id=test_id
    )
    db.session.add(result)
    db.session.commit()
    
    return redirect(url_for('test_result', result_id=result.id))

@app.route('/test_result/<int:result_id>')
def test_result(result_id):
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    result = TestResult.query.get_or_404(result_id)
    return render_template('test_result.html', result=result)

@app.route('/mark_difficult/<int:topic_id>')
def mark_difficult(topic_id):
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    user_id = session['user_id']
    
    # Check if already marked
    existing = DifficultTopic.query.filter_by(user_id=user_id, topic_id=topic_id).first()
    
    if existing:
        db.session.delete(existing)
        flash('Mavzu qiyinlar ro\'yxatidan olib tashlandi', 'info')
    else:
        difficult = DifficultTopic(user_id=user_id, topic_id=topic_id)
        db.session.add(difficult)
        flash('Mavzu qiyinlar ro\'yxatiga qo\'shildi', 'success')
    
    db.session.commit()
    return redirect(request.referrer)

@app.route('/schedule')
def schedule():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    schedules = Schedule.query.filter_by(group_id=user.group_id).all()
    
    return render_template('schedule.html', schedules=schedules)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        group_id = request.form.get('group_id', type=int)
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template('register.html', error="Bu login allaqachon mavjud!")
        
        # Create new student
        new_user = User(
            username=username,
            password_hash=generate_password_hash(password),
            first_name=first_name,
            last_name=last_name,
            group_id=group_id,
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()
        
        flash("Ro'yxatdan o'tdingiz! Endi login qiling.", 'success')
        return redirect(url_for('login'))
    
    groups = Group.query.all()
    return render_template('register.html', groups=groups)

@app.route('/group_rating')
def group_rating():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    
    groups = Group.query.all()
    group_data = []
    
    for group in groups:
        total_students = len([s for s in group.students if not s.is_admin])
        avg_score = 0
        if total_students > 0:
            total_score = sum([s.id for s in group.students if not s.is_admin])  # Placeholder for actual scoring
            avg_score = group.total_score / total_students if total_students > 0 else 0
        
        group_data.append({
            'group': group,
            'total_students': total_students,
            'avg_score': avg_score
        })
    
    group_data.sort(key=lambda x: x['avg_score'], reverse=True)
    
    return render_template('group_rating.html', group_data=group_data)

@app.route('/groups_rating')
def groups_rating():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    
    return redirect(url_for('group_rating'))

@app.route('/upload_certificate', methods=['GET', 'POST'])
def upload_certificate():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        # Create new certificate
        new_certificate = Certificate(
            title=title,
            description=description,
            user_id=session['user_id']
        )
        db.session.add(new_certificate)
        db.session.commit()
        
        flash("Sertifikat muvaffaqiyatli qo'shildi!", 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('upload_certificate.html')

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if not session.get('logged_in', False):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        user = User.query.get(session['user_id'])
        
        if not check_password_hash(user.password_hash, current_password):
            flash("Joriy parol noto'g'ri!", 'error')
            return redirect(url_for('change_password'))
        
        if new_password != confirm_password:
            flash("Yangi parollar mos kelmadi!", 'error')
            return redirect(url_for('change_password'))
        
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()
        
        flash("Parol muvaffaqiyatli o'zgartirildi!", 'success')
        return redirect(url_for('student_dashboard'))
    
    return render_template('change_password.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    print("Starting application...")
    print(f"Python version: {os.sys.version}")
    print(f"Current directory: {os.getcwd()}")
    
    try:
        with app.app_context():
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully!")
            
            # Create admin user if not exists
            admin = User.query.filter_by(username='AkmalJaxonkulov').first()
            if not admin:
                print("Creating admin user...")
                default_group = Group.query.filter_by(id=1).first()
                if not default_group:
                    print("Creating default group...")
                    default_group = Group(id=1, name='Default', total_score=0)
                    db.session.add(default_group)
                    db.session.flush()
                
                admin = User(
                    username='AkmalJaxonkulov',
                    password_hash=generate_password_hash('Akmal1221'),
                    first_name='Akmal',
                    last_name='Jaxonkulov',
                    group_id=1,
                    is_admin=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin user created successfully!")
            else:
                print("Admin user already exists!")
        
        port = int(os.getenv('PORT', 5000))
        print(f"Starting Flask app on port {port}...")
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        print(f"Error during startup: {e}")
        import traceback
        traceback.print_exc()
        raise
