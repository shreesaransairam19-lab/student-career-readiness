"""
Student Skill & Career Readiness Analysis System
Flask + SQLite web application
"""

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash

# Import services
from services.auth import AuthService
from services.scoring import ScoringService
from services.recommendations import RecommendationService

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

DATABASE = os.environ.get(
    'DATABASE_PATH',
    os.path.join(os.path.dirname(__file__), 'database', 'career_readiness.db')
)

# Initialize services
auth_service = AuthService(DATABASE)
scoring_service = ScoringService(DATABASE)
recommendation_service = RecommendationService(DATABASE)


def get_db():
    """Get database connection for current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(error):
    """Close database connection."""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Initialize database from schema."""
    with app.app_context():
        db = get_db()
        with app.open_resource('database/schema.sql', mode='r') as f:
            db.executescript(f.read())
        db.commit()


@app.cli.command('init-db')
def init_db_command():
    """Initialize the database."""
    init_db()
    print('Database initialized.')


@app.cli.command('seed-db')
def seed_db_command():
    """Seed the database with roles, skills, and targets."""
    import subprocess
    result = subprocess.run(['python', 'database/seed.py'], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)


# Template context processors
@app.context_processor
def inject_current_user():
    """Inject current user into all templates."""
    user_id = session.get('user_id')
    if user_id:
        user = auth_service.get_user_by_id(user_id)
        return {'current_user': user}
    return {'current_user': None}


@app.context_processor
def inject_nav_pages():
    """Inject navigation pages into all templates."""
    pages = [
        ('profile', 'Profile'),
        ('assessment', 'Assessment'),
        ('dashboard', 'Dashboard'),
        ('projects', 'Projects'),
        ('history', 'History'),
    ]
    return {'nav_pages': pages}


# Authentication routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        name = request.form['name'].strip()
        
        if not email or not password or not name:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        try:
            user_id = auth_service.register(email, password, name)
            session['user_id'] = user_id
            flash('Registration successful!', 'success')
            return redirect(url_for('profile'))
        except ValueError as e:
            flash(str(e), 'error')
    
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        
        user = auth_service.login(email, password)
        if user:
            session['user_id'] = user['id']
            flash('Login successful!', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


# Protected route decorator
def login_required(f):
    """Decorator to require login for routes."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
        if not user_id or not auth_service.get_user_by_id(user_id):
            session.clear()
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# Main application routes
@app.route('/')
@login_required
def index():
    return redirect(url_for('profile'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    
    if request.method == 'POST':
        name = request.form['name'].strip()
        department = request.form['department'].strip()
        study_year = request.form['study_year']
        career_goal = request.form['career_goal']
        
        if not name:
            flash('Name is required.', 'error')
        else:
            try:
                study_year_int = int(study_year) if study_year else None
            except ValueError:
                flash('Study year must be a number.', 'error')
                study_year_int = None
            
            if study_year_int is not None or not study_year:
                auth_service.update_profile(user_id, name, department, study_year_int, career_goal)
                flash('Profile updated.', 'success')
                return redirect(url_for('profile'))
    
    user = auth_service.get_user_by_id(user_id)
    roles = auth_service.get_all_roles()
    return render_template('profile.html', user=user, roles=roles, departments=['CSE', 'AIDS'], years=[1,2,3,4,5,6,7,8])


@app.route('/assessment')
@login_required
def assessment():
    user_id = session['user_id']
    user = auth_service.get_user_by_id(user_id)
    
    if not user['career_goal']:
        flash('Please select a target role in your profile first.', 'error')
        return redirect(url_for('profile'))
    
    role = auth_service.get_role_by_name(user['career_goal'])
    if not role:
        flash('Invalid target role.', 'error')
        return redirect(url_for('profile'))
    
    skills = scoring_service.get_skills_for_role(role['id'])
    return render_template('assessment.html', role=role, skills=skills)


@app.route('/assessment/submit', methods=['POST'])
@login_required
def submit_assessment():
    user_id = session['user_id']
    user = auth_service.get_user_by_id(user_id)
    
    if not user['career_goal']:
        flash('Please select a target role in your profile first.', 'error')
        return redirect(url_for('profile'))
    
    role = auth_service.get_role_by_name(user['career_goal'])
    skills = scoring_service.get_skills_for_role(role['id'])
    
    # Collect ratings; reject any submitted value outside 1-5
    ratings = {}
    for skill in skills:
        rating_key = f"skill_{skill['id']}"
        raw = request.form.get(rating_key, "")
        if raw == "":
            continue
        try:
            rating = int(raw)
        except ValueError:
            flash(f'Invalid rating submitted for {skill["name"]}.', 'error')
            return redirect(url_for('assessment'))
        if rating < 1 or rating > 5:
            flash(f'Rating for {skill["name"]} must be between 1 and 5.', 'error')
            return redirect(url_for('assessment'))
        ratings[skill['id']] = rating
    
    # Validate at least one rating
    if not ratings:
        flash('Please rate at least one skill.', 'error')
        return redirect(url_for('assessment'))
    
    # Save assessment
    assessment_id = scoring_service.save_assessment(user_id, role['id'], ratings)
    flash('Assessment saved successfully!', 'success')
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    user_id = session['user_id']
    user = auth_service.get_user_by_id(user_id)
    
    if not user['career_goal']:
        flash('Please select a target role in your profile first.', 'error')
        return redirect(url_for('profile'))
    
    role = auth_service.get_role_by_name(user['career_goal'])
    if not role:
        flash('Invalid target role.', 'error')
        return redirect(url_for('profile'))
    
    # Get latest assessment
    latest_assessment = scoring_service.get_latest_assessment(user_id, role['id'])
    if not latest_assessment:
        flash('No assessment found. Please complete an assessment first.', 'error')
        return redirect(url_for('assessment'))
    
    # Compute scoring data
    gaps = scoring_service.compute_gaps(user_id, role['id'], latest_assessment['id'], include_projects=True)
    category_averages = scoring_service.compute_category_averages(user_id, role['id'], latest_assessment['id'], include_projects=True)
    readiness_percentage = scoring_service.compute_readiness_percentage(category_averages)
    
    # Get projects for context
    projects = auth_service.get_user_projects(user_id)
    recommendations = recommendation_service.get_recommendations(gaps, user_id, len(projects))
    
    return render_template('dashboard.html', 
                         user=user,
                         role=role,
                         assessment=latest_assessment,
                         gaps=gaps,
                         category_averages=category_averages,
                         readiness_percentage=readiness_percentage,
                         recommendations=recommendations,
                         projects=projects)


@app.route('/projects', methods=['GET', 'POST'])
@login_required
def projects():
    user_id = session['user_id']
    
    if request.method == 'POST':
        title = request.form['title'].strip()
        description = request.form['description'].strip()
        technologies = request.form['technologies'].strip()
        project_url = request.form['project_url'].strip()
        
        if not title:
            flash('Project title is required.', 'error')
        else:
            auth_service.add_project(user_id, title, description, technologies, project_url)
            flash('Project added.', 'success')
            return redirect(url_for('projects'))
    
    user_projects = auth_service.get_user_projects(user_id)
    return render_template('projects.html', projects=user_projects)


@app.route('/history')
@login_required
def history():
    user_id = session['user_id']
    user = auth_service.get_user_by_id(user_id)
    
    if not user['career_goal']:
        flash('Please select a target role in your profile first.', 'error')
        return redirect(url_for('profile'))
    
    role = auth_service.get_role_by_name(user['career_goal'])
    assessments = scoring_service.get_assessment_history(user_id, role['id'])
    
    return render_template('history.html', assessments=assessments, role=role)


@app.route('/history/<int:assessment_id>')
@login_required
def view_assessment(assessment_id):
    user_id = session['user_id']
    user = auth_service.get_user_by_id(user_id)
    
    if not user['career_goal']:
        return redirect(url_for('profile'))
    
    role = auth_service.get_role_by_name(user['career_goal'])
    assessment = scoring_service.get_assessment_by_id(user_id, role['id'], assessment_id)
    
    if not assessment:
        flash('Assessment not found.', 'error')
        return redirect(url_for('history'))
    
    # Compute scoring data for this historical assessment
    gaps = scoring_service.compute_gaps(user_id, role['id'], assessment_id, include_projects=True)
    category_averages = scoring_service.compute_category_averages(user_id, role['id'], assessment_id, include_projects=True)
    readiness_percentage = scoring_service.compute_readiness_percentage(category_averages)
    user_projects = auth_service.get_user_projects(user_id)
    recommendations = recommendation_service.get_recommendations(gaps, user_id, len(user_projects))
    
    return render_template('dashboard.html',
                         user=user,
                         role=role,
                         assessment=assessment,
                         gaps=gaps,
                         category_averages=category_averages,
                         readiness_percentage=readiness_percentage,
                         recommendations=recommendations,
                         projects=[],  # No projects in historical view
                         is_history=True)


if __name__ == '__main__':
    app.run(debug=True)