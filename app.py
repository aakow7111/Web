import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# CRITICAL: Set secret key for sessions to work
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

# Routes
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        print(f"Login attempt: username={username}")
        
        # Simple hardcoded admin login
        if username == 'AkmalJaxonkulov' and password == 'Akmal1221':
            print("Admin login successful!")
            
            # Create admin user if not exists
            admin_user = User.query.filter_by(username='AkmalJaxonkulov').first()
            if not admin_user:
                print("Creating admin user...")
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
                print("Admin user created!")
            
            # Store user in session
            session['user_id'] = admin_user.id
            session['username'] = admin_user.username
            session['is_admin'] = admin_user.is_admin
            session['logged_in'] = True  # Additional flag
            
            print(f"Session created: user_id={session.get('user_id')}, username={session.get('username')}")
            print("Redirecting to admin dashboard...")
            
            # Test session
            print(f"Session test: {dict(session)}")
            
            return redirect(url_for('admin_dashboard'))
        
        print("Login failed!")
        return render_template('login.html', error="Login yoki parol noto'g'ri!")
    
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    print(f"Admin dashboard accessed. Session: {dict(session)}")
    
    # Check if user is logged in via session
    if not session.get('logged_in', False):
        print("User not logged in, redirecting to login")
        return redirect(url_for('login'))
    
    if not session.get('is_admin', False):
        print("User is not admin, redirecting to login")
        return redirect(url_for('login'))
    
    print(f"Admin dashboard accessed by: {session.get('username')}")
    
    total_students = User.query.filter_by(is_admin=False).count()
    total_groups = Group.query.count()
    total_tests = Test.query.count()
    
    print(f"Stats: students={total_students}, groups={total_groups}, tests={total_tests}")
    
    return render_template('simple_admin_dashboard.html',
                         total_students=total_students,
                         total_groups=total_groups,
                         total_tests=total_tests)

@app.route('/logout')
def logout():
    session.clear()
    print("Session cleared, redirecting to login")
    return redirect(url_for('login'))

@app.route('/test')
def test():
    return f"Test route - Session: {dict(session)}"

if __name__ == '__main__':
    print("Starting application...")
    print(f"Python version: {os.sys.version}")
    print(f"Current directory: {os.getcwd()}")
    print(f"SECRET_KEY: {app.config['SECRET_KEY']}")
    
    try:
        with app.app_context():
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully!")
            
            # Create admin user if not exists
            admin = User.query.filter_by(username='AkmalJaxonkulov').first()
            if not admin:
                print("Creating admin user...")
                # First create a default group if it doesn't exist
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
