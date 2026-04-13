import os
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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
        try:
            # Get form data
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '').strip()
            
            print(f"Login attempt: username='{username}', password_length={len(password)}")
            
            # Simple hardcoded admin check
            if username == 'AkmalJaxonkulov' and password == 'Akmal1221':
                print("Admin credentials correct!")
                
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
                
                # Store in session
                session.clear()
                session['user_id'] = admin_user.id
                session['username'] = admin_user.username
                session['is_admin'] = admin_user.is_admin
                session['logged_in'] = True
                session.permanent = True
                
                print(f"Session data: {dict(session)}")
                print("Redirecting to admin dashboard...")
                
                return redirect(url_for('admin_dashboard'))
            else:
                print("Invalid credentials!")
                return render_template('login.html', error="Login yoki parol noto'g'ri!")
                
        except Exception as e:
            print(f"Login error: {e}")
            import traceback
            traceback.print_exc()
            return render_template('login.html', error="Xatolik yuz berdi!")
    
    return render_template('login.html')

@app.route('/admin')
def admin_dashboard():
    print(f"Admin dashboard accessed. Session: {dict(session)}")
    
    # Check session
    if not session.get('logged_in', False):
        print("Not logged in, redirecting to login")
        return redirect(url_for('login'))
    
    if not session.get('is_admin', False):
        print("Not admin, redirecting to login")
        return redirect(url_for('login'))
    
    try:
        total_students = User.query.filter_by(is_admin=False).count()
        total_groups = Group.query.count()
        total_tests = Test.query.count()
        
        print(f"Stats calculated: students={total_students}, groups={total_groups}, tests={total_tests}")
        
        return render_template('simple_admin_dashboard.html',
                             total_students=total_students,
                             total_groups=total_groups,
                             total_tests=total_tests)
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('simple_admin_dashboard.html',
                             total_students=0,
                             total_groups=0,
                             total_tests=0)

@app.route('/logout')
def logout():
    session.clear()
    print("Logged out, session cleared")
    return redirect(url_for('login'))

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        print(f"API Login attempt: username='{username}'")
        
        if username == 'AkmalJaxonkulov' and password == 'Akmal1221':
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
            
            return jsonify({'success': True, 'redirect': url_for('admin_dashboard')})
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'})
            
    except Exception as e:
        print(f"API Login error: {e}")
        return jsonify({'success': False, 'error': 'Server error'})

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
