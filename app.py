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

@app.route('/admin/groups')
def admin_groups():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    groups = Group.query.all()
    return render_template('admin_groups.html', groups=groups)

@app.route('/admin/subjects')
def admin_subjects():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    subjects = Subject.query.all()
    return render_template('admin_subjects.html', subjects=subjects)

@app.route('/admin/tests')
def admin_tests():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    tests = Test.query.all()
    subjects = Subject.query.all()
    return render_template('admin_tests.html', tests=tests, subjects=subjects)

@app.route('/admin/schedule')
def admin_schedule():
    if not session.get('logged_in', False) or not session.get('is_admin', False):
        return redirect(url_for('login'))
    schedules = Schedule.query.all()
    groups = Group.query.all()
    return render_template('admin_schedule.html', schedules=schedules, groups=groups)

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
