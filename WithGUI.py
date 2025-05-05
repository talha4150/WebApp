from flask import Flask, request, render_template_string, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from azure.storage.blob import BlobServiceClient, ContentSettings
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'f1340841002453968837b6053f9dc3fdc7fd3b7d86b87dca'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://admin1:admin999%40@videosharingtalha3.database.windows.net/videosharingtalha2?driver=ODBC+Driver+17+for+SQL+Server'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Azure Blob Storage
AZURE_CONNECTION_STRING = 'DefaultEndpointsProtocol=https;AccountName=videosharingtalha;AccountKey=0+oNtBOsIJcaAapgXe+jrWtCalOm2UAzQErO3pkYiNLAl+RmGbnVR81BkfoWpEGY7x4PzBtMLEMV+AStJDxQjQ==;EndpointSuffix=core.windows.net'
AZURE_CONTAINER_NAME = 'uploads'

db = SQLAlchemy(app)
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
try:
    blob_service_client.create_container(AZURE_CONTAINER_NAME)
except Exception:
    pass

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(512), nullable=False)

class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    caption = db.Column(db.String(256), nullable=True)
    location = db.Column(db.String(100), nullable=True)
    people_present = db.Column(db.String(256), nullable=True)
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    file_path = db.Column(db.String(512), nullable=False)
    media_type = db.Column(db.String(20), nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='media')
    ratings = db.relationship('Rating', backref='media')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    value = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    __table_args__ = (db.UniqueConstraint('user_id', 'media_id', name='unique_user_media_rating'),)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>StreamScape</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                :root {
                    --primary: #4f46e5;
                    --primary-hover: #6366f1;
                    --secondary: #10b981;
                    --background: #f9fafb;
                    --surface: #ffffff;
                    --text-primary: #111827;
                    --text-secondary: #6b7280;
                    --border: #e5e7eb;
                    --error: #ef4444;
                    --success: #22c55e;
                }

                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                    font-family: 'Inter', sans-serif;
                }

                body {
                    background-color: var(--background);
                    color: var(--text-primary);
                    line-height: 1.6;
                    min-height: 100vh;
                }

                .container {
                    max-width: 1280px;
                    margin: 0 auto;
                    padding: 0 1.5rem;
                }

                .btn {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: 0.75rem 1.5rem;
                    border-radius: 9999px;
                    background-color: var(--primary);
                    color: white;
                    font-weight: 600;
                    text-decoration: none;
                    transition: all 0.3s ease;
                }

                .btn:hover {
                    background-color: var(--primary-hover);
                    transform: translateY(-2px);
                }

                .btn-secondary {
                    background-color: transparent;
                    border: 2px solid var(--primary);
                    color: var(--primary);
                }

                .btn-secondary:hover {
                    background-color: var(--primary);
                    color: white;
                }

                .hero {
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    align-items: center;
                    text-align: center;
                    background-image: url('https://images.pexels.com/photos/3184291/pexels-photo-3184291.jpeg');
                    background-size: cover;
                    background-position: center;
                    position: relative;
                }

                .hero::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.4);
                }

                .hero-content {
                    position: relative;
                    z-index: 1;
                }

                .hero-title {
                    font-size: 3.5rem;
                    font-weight: 800;
                    margin-bottom: 1.5rem;
                    color: white;
                    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                }

                .hero-subtitle {
                    font-size: 1.25rem;
                    margin-bottom: 2.5rem;
                    color: #e5e7eb;
                    max-width: 600px;
                }

                .hero-buttons {
                    display: flex;
                    gap: 1.5rem;
                }

                @keyframes fadeIn {
                    from { opacity: 0; transform: translateY(20px); }
                    to { opacity: 1; transform: translateY(0); }
                }

                .animate-fade-in {
                    animation: fadeIn 0.5s ease forwards;
                }

                @media (max-width: 768px) {
                    .hero-title {
                        font-size: 2.5rem;
                    }

                    .hero-subtitle {
                        font-size: 1rem;
                    }

                    .hero-buttons {
                        flex-direction: column;
                        gap: 1rem;
                    }
                }
            </style>
        </head>
        <body>
            <div class="hero">
                <div class="hero-content">
                    <h1 class="hero-title animate-fade-in">Welcome to StreamScape</h1>
                    <p class="hero-subtitle animate-fade-in" style="animation-delay: 0.2s;">Connect, share, and explore captivating videos and photos in a vibrant community.</p>
                    <div class="hero-buttons animate-fade-in" style="animation-delay: 0.4s;">
                        <a href="{{ url_for('login') }}" class="btn">Log In</a>
                        <a href="{{ url_for('register') }}" class="btn btn-secondary">Sign Up</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
    ''')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, role=role, password=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('login'))
        except IntegrityError:
            db.session.rollback()
            flash('Username or email already exists.', 'error')
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Register - StreamScape</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                :root {
                    --primary: #4f46e5;
                    --primary-hover: #6366f1;
                    --secondary: #10b981;
                    --background: #f9fafb;
                    --surface: #ffffff;
                    --text-primary: #111827;
                    --text-secondary: #6b7280;
                    --border: #e5e7eb;
                    --error: #ef4444;
                    --success: #22c55e;
                }

                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                    font-family: 'Inter', sans-serif;
                }

                body {
                    background-color: var(--background);
                    color: var(--text-primary);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                }

                .auth-container {
                    display: flex;
                    max-width: 900px;
                    margin: 2rem auto;
                    background: var(--surface);
                    border-radius: 1rem;
                    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }

                .auth-image {
                    flex: 1;
                    background-image: url('https://images.pexels.com/photos/3184292/pexels-photo-3184292.jpeg');
                    background-size: cover;
                    background-position: center;
                    position: relative;
                    display: none;
                }

                .auth-image::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.3);
                }

                .auth-form {
                    flex: 1;
                    padding: 3rem;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }

                .auth-title {
                    font-size: 2rem;
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                }

                .auth-subtitle {
                    color: var(--text-secondary);
                    margin-bottom: 2rem;
                }

                .form-group {
                    margin-bottom: 1.5rem;
                }

                .form-label {
                    display: block;
                    font-weight: 500;
                    margin-bottom: 0.5rem;
                    color: var(--text-primary);
                }

                .input {
                    width: 100%;
                    padding: 0.75rem 1rem;
                    border-radius: 0.5rem;
                    border: 1px solid var(--border);
                    background: var(--surface);
                    color: var(--text-primary);
                    font-size: 1rem;
                    transition: all 0.3s ease;
                }

                .input:focus {
                    outline: none;
                    border-color: var(--primary);
                    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
                }

                .role-selector {
                    display: flex;
                    gap: 1rem;
                    margin-bottom: 1.5rem;
                }

                .role-option {
                    flex: 1;
                    position: relative;
                }

                .role-option input {
                    position: absolute;
                    opacity: 0;
                    cursor: pointer;
                }

                .role-option label {
                    display: block;
                    padding: 1rem;
                    border-radius: 0.5rem;
                    border: 2px solid var(--border);
                    text-align: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                }

                .role-option input:checked + label {
                    border-color: var(--primary);
                    background: rgba(79, 70, 229, 0.05);
                }

                .role-title {
                    font-weight: 600;
                    margin-bottom: 0.25rem;
                }

                .role-desc {
                    font-size: 0.875rem;
                    color: var(--text-secondary);
                }

                .btn {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: 0.75rem 1.5rem;
                    border-radius: 9999px;
                    background-color: var(--primary);
                    color: white;
                    font-weight: 600;
                    text-decoration: none;
                    transition: all 0.3s ease;
                    width: 100%;
                }

                .btn:hover {
                    background-color: var(--primary-hover);
                    transform: translateY(-2px);
                }

                .auth-footer {
                    margin-top: 1.5rem;
                    text-align: center;
                    color: var(--text-secondary);
                }

                .auth-footer a {
                    color: var(--primary);
                    text-decoration: none;
                    font-weight: 500;
                }

                .alert {
                    padding: 1rem;
                    border-radius: 0.5rem;
                    margin-bottom: 1.5rem;
                }

                .alert-success {
                    background-color: rgba(34, 197, 94, 0.1);
                    color: var(--success);
                    border: 1px solid var(--success);
                }

                .alert-error {
                    background-color: rgba(239, 68, 68, 0.1);
                    color: var(--error);
                    border: 1px solid var(--error);
                }

                @media (min-width: 768px) {
                    .auth-image {
                        display: block;
                    }
                }

                @media (max-width: 640px) {
                    .auth-container {
                        margin: 1rem;
                        flex-direction: column;
                    }

                    .auth-form {
                        padding: 2rem;
                    }
                }
            </style>
        </head>
        <body>
            <div class="auth-container">
                <div class="auth-image"></div>
                <div class="auth-form">
                    <h1 class="auth-title">Join StreamScape</h1>
                    <p class="auth-subtitle">Create your account to start sharing and exploring.</p>

                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ category }}">{{ message }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}

                    <form method="POST" action="{{ url_for('register') }}">
                        <div class="form-group">
                            <label class="form-label" for="username">Username</label>
                            <input type="text" name="username" id="username" class="input" placeholder="Choose a username" required>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="email">Email</label>
                            <input type="email" name="email" id="email" class="input" placeholder="Your email address" required>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="password">Password</label>
                            <input type="password" name="password" id="password" class="input" placeholder="Create a password" required>
                        </div>

                        <div class="form-group">
                            <label class="form-label">Account Type</label>
                            <div class="role-selector">
                                <div class="role-option">
                                    <input type="radio" id="creator" name="role" value="creator" checked>
                                    <label for="creator">
                                        <div class="role-title">Creator</div>
                                        <div class="role-desc">Share your own content</div>
                                    </label>
                                </div>
                                <div class="role-option">
                                    <input type="radio" id="consumer" name="role" value="consumer">
                                    <label for="consumer">
                                        <div class="role-title">Consumer</div>
                                        <div class="role-desc">Explore and enjoy content</div>
                                    </label>
                                </div>
                            </div>
                        </div>

                        <button type="submit" class="btn">Create Account</button>
                    </form>

                    <div class="auth-footer">
                        Already have an account? <a href="{{ url_for('login') }}">Log In</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
    ''')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            session['username'] = user.username
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Login - StreamScape</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                :root {
                    --primary: #4f46e5;
                    --primary-hover: #6366f1;
                    --secondary: #10b981;
                    --background: #f9fafb;
                    --surface: #ffffff;
                    --text-primary: #111827;
                    --text-secondary: #6b7280;
                    --border: #e5e7eb;
                    --error: #ef4444;
                    --success: #22c55e;
                }

                * {
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                    font-family: 'Inter', sans-serif;
                }

                body {
                    background-color: var(--background);
                    color: var(--text-primary);
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                }

                .auth-container {
                    display: flex;
                    max-width: 900px;
                    margin: 2rem auto;
                    background: var(--surface);
                    border-radius: 1rem;
                    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }

                .auth-image {
                    flex: 1;
                    background-image: url('https://images.pexels.com/photos/3184296/pexels-photo-3184296.jpeg');
                    background-size: cover;
                    background-position: center;
                    position: relative;
                    display: none;
                }

                .auth-image::before {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.3);
                }

                .auth-form {
                    flex: 1;
                    padding: 3rem;
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                }

                .auth-title {
                    font-size: 2rem;
                    font-weight: 700;
                    margin-bottom: 0.5rem;
                }

                .auth-subtitle {
                    color: var(--text-secondary);
                    margin-bottom: 2rem;
                }

                .form-group {
                    margin-bottom: 1.5rem;
                }

                .form-label {
                    display: block;
                    font-weight: 500;
                    margin-bottom: 0.5rem;
                    color: var(--text-primary);
                }

                .input {
                    width: 100%;
                    padding: 0.75rem 1rem;
                    border-radius: 0.5rem;
                    border: 1px solid var(--border);
                    background: var(--surface);
                    color: var(--text-primary);
                    font-size: 1rem;
                    transition: all 0.3s ease;
                }

                .input:focus {
                    outline: none;
                    border-color: var(--primary);
                    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
                }

                .btn {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    padding: 0.75rem 1.5rem;
                    border-radius: 9999px;
                    background-color: var(--primary);
                    color: white;
                    font-weight: 600;
                    text-decoration: none;
                    transition: all 0.3s ease;
                    width: 100%;
                }

                .btn:hover {
                    background-color: var(--primary-hover);
                    transform: translateY(-2px);
                }

                .auth-footer {
                    margin-top: 1.5rem;
                    text-align: center;
                    color: var(--text-secondary);
                }

                .auth-footer a {
                    color: var(--primary);
                    text-decoration: none;
                    font-weight: 500;
                }

                .alert {
                    padding: 1rem;
                    border-radius: 0.5rem;
                    margin-bottom: 1.5rem;
                }

                .alert-success {
                    background-color: rgba(34, 197, 94, 0.1);
                    color: var(--success);
                    border: 1px solid var(--success);
                }

                .alert-error {
                    background-color: rgba(239, 68, 68, 0.1);
                    color: var(--error);
                    border: 1px solid var(--error);
                }

                @media (min-width: 768px) {
                    .auth-image {
                        display: block;
                    }
                }

                @media (max-width: 640px) {
                    .auth-container {
                        margin: 1rem;
                        flex-direction: column;
                    }

                    .auth-form {
                        padding: 2rem;
                    }
                }
            </style>
        </head>
        <body>
            <div class="auth-container">
                <div class="auth-image"></div>
                <div class="auth-form">
                    <h1 class="auth-title">Welcome Back</h1>
                    <p class="auth-subtitle">Log in to continue your StreamScape journey.</p>

                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ category }}">{{ message }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}

                    <form method="POST" action="{{ url_for('login') }}">
                        <div class="form-group">
                            <label class="form-label" for="username">Username</label>
                            <input type="text" name="username" id="username" class="input" placeholder="Your username" required>
                        </div>

                        <div class="form-group">
                            <label class="form-label" for="password">Password</label>
                            <input type="password" name="password" id="password" class="input" placeholder="Your password" required>
                        </div>

                        <button type="submit" class="btn">Log In</button>
                    </form>

                    <div class="auth-footer">
                        Don't have an account? <a href="{{ url_for('register') }}">Sign Up</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
    ''')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    search_query = request.form.get('search_query', '')
    media = Media.query.filter(Media.title.contains(search_query)).options(
        joinedload(Media.comments),
        joinedload(Media.ratings)
    ).all()

    if session['role'] == 'creator':
        return render_template_string('''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Creator Dashboard - StreamScape</title>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
                <style>
                    :root {
                        --primary: #4f46e5;
                        --primary-hover: #6366f1;
                        --secondary: #10b981;
                        --background: #f9fafb;
                        --surface: #ffffff;
                        --text-primary: #111827;
                        --text-secondary: #6b7280;
                        --border: #e5e7eb;
                        --error: #ef4444;
                        --success: #22c55e;
                    }

                    * {
                        box-sizing: border-box;
                        margin: 0;
                        padding: 0;
                        font-family: 'Inter', sans-serif;
                    }

                    body {
                        background-color: var(--background);
                        color: var(--text-primary);
                        min-height: 100vh;
                    }

                    .dashboard {
                        display: flex;
                        min-height: 100vh;
                    }

                    .sidebar {
                        width: 250px;
                        background: var(--surface);
                        padding: 1.5rem;
                        border-right: 1px solid var(--border);
                    }

                    .sidebar-logo {
                        font-size: 1.5rem;
                        font-weight: 700;
                        color: var(--primary);
                        margin-bottom: 2rem;
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                    }

                    .sidebar-menu {
                        display: flex;
                        flex-direction: column;
                        gap: 0.25rem;
                    }

                    .sidebar-link {
                        display: flex;
                        align-items: center;
                        gap: 0.75rem;
                        padding: 0.75rem 1rem;
                        border-radius: 0.5rem;
                        color: var(--text-secondary);
                        text-decoration: none;
                        transition: all 0.3s ease;
                    }

                    .sidebar-link:hover, .sidebar-link.active {
                        background: var(--primary);
                        color: white;
                    }

                    .main-content {
                        flex: 1;
                        padding: 2rem;
                    }

                    .dashboard-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        margin-bottom: 2rem;
                    }

                    .dashboard-title {
                        font-size: 1.75rem;
                        font-weight: 700;
                    }

                    .user-profile {
                        display: flex;
                        align-items: center;
                        gap: 0.75rem;
                    }

                    .user-avatar {
                        width: 2.5rem;
                        height: 2.5rem;
                        border-radius: 50%;
                        background: var(--primary);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        color: white;
                        font-weight: 600;
                    }

                    .panel {
                        background: var(--surface);
                        border-radius: 1rem;
                        padding: 2rem;
                        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
                        margin-bottom: 2rem;
                    }

                    .panel-title {
                        font-size: 1.25rem;
                        font-weight: 600;
                        margin-bottom: 1.5rem;
                    }

                    .form-group {
                        margin-bottom: 1.5rem;
                    }

                    .form-label {
                        display: block;
                        font-weight: 500;
                        margin-bottom: 0.5rem;
                    }

                    .input, select, textarea {
                        width: 100%;
                        padding: 0.75rem 1rem;
                        border-radius: 0.5rem;
                        border: 1px solid var(--border);
                        background: var(--surface);
                        color: var(--text-primary);
                        font-size: 1rem;
                        transition: all 0.3s ease;
                    }

                    .input:focus, select:focus, textarea:focus {
                        outline: none;
                        border-color: var(--primary);
                        box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
                    }

                    .upload-container {
                        border: 2px dashed var(--border);
                        border-radius: 0.5rem;
                        padding: 2rem;
                        text-align: center;
                        transition: all 0.3s ease;
                        cursor: pointer;
                    }

                    .upload-container:hover {
                        border-color: var(--primary);
                        background: rgba(79, 70, 229, 0.05);
                    }

                    .upload-icon {
                        font-size: 2.5rem;
                        color: var(--primary);
                        margin-bottom: 1rem;
                    }

                    .upload-text {
                        margin-bottom: 1rem;
                        color: var(--text-secondary);
                    }

                    .file-input {
                        display: none;
                    }

                    .btn {
                        display: inline-flex;
                        align-items: center;
                        justify-content: center;
                        padding: 0.75rem 1.5rem;
                        border-radius: 9999px;
                        background-color: var(--primary);
                        color: white;
                        font-weight: 600;
                        text-decoration: none;
                        transition: all 0.3s ease;
                    }

                    .btn:hover {
                        background-color: var(--primary-hover);
                        transform: translateY(-2px);
                    }

                    .alert {
                        padding: 1rem;
                        border-radius: 0.5rem;
                        margin-bottom: 1.5rem;
                    }

                    .alert-success {
                        background-color: rgba(34, 197, 94, 0.1);
                        color: var(--success);
                        border: 1px solid var(--success);
                    }

                    .alert-error {
                        background-color: rgba(239, 68, 68, 0.1);
                        color: var(--error);
                        border: 1px solid var(--error);
                    }

                    @media (max-width: 768px) {
                        .dashboard {
                            flex-direction: column;
                        }

                        .sidebar {
                            width: 100%;
                            border-right: none;
                            border-bottom: 1px solid var(--border);
                        }
                    }
                </style>
            </head>
            <body>
                <div class="dashboard">
                    <div class="sidebar">
                        <div class="sidebar-logo">
                            <i class="fas fa-photo-film"></i>
                            StreamScape
                        </div>
                        <nav class="sidebar-menu">
                            <a href="{{ url_for('dashboard') }}" class="sidebar-link active">
                                <i class="fas fa-home"></i> Dashboard
                            </a>
                            <a href="{{ url_for('logout') }}" class="sidebar-link">
                                <i class="fas fa-sign-out-alt"></i> Logout
                            </a>
                        </nav>
                    </div>
                    <div class="main-content">
                        <div class="dashboard-header">
                            <h1 class="dashboard-title">Creator Dashboard</h1>
                            <div class="user-profile">
                                <div class="user-avatar">
                                    {{ session.username[0] if session.username else 'U' }}
                                </div>
                                <span>{{ session.username or 'Creator' }}</span>
                            </div>
                        </div>

                        {% with messages = get_flashed_messages(with_categories=true) %}
                            {% if messages %}
                                {% for category, message in messages %}
                                    <div class="alert alert-{{ category }}">{{ message }}</div>
                                {% endfor %}
                            {% endif %}
                        {% endwith %}

                        <div class="panel">
                            <h2 class="panel-title">Upload New Media</h2>
                            <form method="POST" action="{{ url_for('upload') }}" enctype="multipart/form-data">
                                <div class="form-group">
                                    <label class="form-label">Title</label>
                                    <input type="text" name="title" class="input" placeholder="Give your media a title" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Caption</label>
                                    <textarea name="caption" class="input" placeholder="Add a caption" rows="3"></textarea>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Location</label>
                                    <input type="text" name="location" class="input" placeholder="Where was this taken?">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">People Present</label>
                                    <input type="text" name="people_present" class="input" placeholder="Who's in this media?">
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Media Type</label>
                                    <select name="media_type" class="input" required>
                                        <option value="video">Video</option>
                                        <option value="picture">Picture</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">File</label>
                                    <div class="upload-container" id="dropzone" onclick="document.getElementById('file-input').click()">
                                        <i class="fas fa-cloud-upload-alt upload-icon"></i>
                                        <p class="upload-text">Drag & drop or click to browse</p>
                                        <input type="file" name="file" id="file-input" class="file-input" required>
                                        <p id="selected-file">No file selected</p>
                                    </div>
                                </div>
                                <button type="submit" class="btn">Upload Media</button>
                            </form>
                        </div>
                    </div>
                </div>
                <script>
                    const fileInput = document.getElementById('file-input');
                    const selectedFile = document.getElementById('selected-file');
                    const dropzone = document.getElementById('dropzone');

                    fileInput.addEventListener('change', () => {
                        selectedFile.textContent = fileInput.files.length > 0 ? fileInput.files[0].name : 'No file selected';
                    });

                    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                        dropzone.addEventListener(eventName, e => {
                            e.preventDefault();
                            e.stopPropagation();
                        }, false);
                    });

                    ['dragenter', 'dragover'].forEach(eventName => {
                        dropzone.addEventListener(eventName, () => {
                            dropzone.style.borderColor = 'var(--primary)';
                            dropzone.style.backgroundColor = 'rgba(79, 70, 229, 0.05)';
                        }, false);
                    });

                    ['dragleave', 'drop'].forEach(eventName => {
                        dropzone.addEventListener(eventName, () => {
                            dropzone.style.borderColor = 'var(--border)';
                            dropzone.style.backgroundColor = 'transparent';
                        }, false);
                    });

                    dropzone.addEventListener('drop', e => {
                        const files = e.dataTransfer.files;
                        fileInput.files = files;
                        if (files.length > 0) {
                            selectedFile.textContent = files[0].name;
                        }
                    });
                </script>
            </body>
            </html>
        ''')

    else:
        return render_template_string('''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Discover Media - StreamScape</title>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
                <style>
                    :root {
                        --primary: #4f46e5;
                        --primary-hover: #6366f1;
                        --secondary: #10b981;
                        --background: #f9fafb;
                        --surface: #ffffff;
                        --text-primary: #111827;
                        --text-secondary: #6b7280;
                        --border: #e5e7eb;
                        --error: #ef4444;
                        --success: #22c55e;
                    }

                    * {
                        box-sizing: border-box;
                        margin: 0;
                        padding: 0;
                        font-family: 'Inter', sans-serif;
                    }

                    body {
                        background-color: var(--background);
                        color: var(--text-primary);
                        min-height: 100vh;
                    }

                    .header {
                        background: var(--surface);
                        padding: 1.5rem 0;
                        border-bottom: 1px solid var(--border);
                    }

                    .header-container {
                        max-width: 1280px;
                        margin: 0 auto;
                        padding: 0 1.5rem;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }

                    .logo {
                        font-size: 1.5rem;
                        font-weight: 700;
                        color: var(--primary);
                        text-decoration: none;
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                    }

                    .nav-links {
                        display: flex;
                        gap: 1.5rem;
                    }

                    .nav-link {
                        color: var(--text-secondary);
                        text-decoration: none;
                        display: flex;
                        align-items: center;
                        gap: 0.25rem;
                        transition: color 0.3s ease;
                    }

                    .nav-link:hover, .nav-link.active {
                        color: var(--primary);
                    }

                    .search-container {
                        max-width: 1280px;
                        margin: 2rem auto;
                        padding: 0 1.5rem;
                    }

                    .search-form {
                        display: flex;
                        gap: 0.5rem;
                    }

                    .search-input {
                        flex: 1;
                        padding: 0.75rem 1.25rem;
                        border-radius: 9999px;
                        border: 1px solid var(--border);
                        background: var(--surface);
                        color: var(--text-primary);
                        font-size: 1rem;
                    }

                    .search-btn {
                        padding: 0 1.5rem;
                        border-radius: 9999px;
                        background: var(--primary);
                        color: white;
                        border: none;
                        font-weight: 600;
                        transition: all 0.3s ease;
                    }

                    .search-btn:hover {
                        background: var(--primary-hover);
                    }

                    .media-grid {
                        max-width: 1280px;
                        margin: 0 auto;
                        padding: 0 1.5rem;
                        display: grid;
                        gap: 2rem;
                        grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    }

                    .media-item {
                        background: var(--surface);
                        border-radius: 1rem;
                        overflow: hidden;
                        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
                        transition: transform 0.3s ease;
                    }

                    .media-item:hover {
                        transform: translateY(-5px);
                    }

                    .media-preview {
                        width: 100%;
                        aspect-ratio: 16/9;
                        object-fit: cover;
                    }

                    .media-info {
                        padding: 1.25rem;
                    }

                    .media-title {
                        font-size: 1.125rem;
                        font-weight: 600;
                        margin-bottom: 0.5rem;
                    }

                    .media-caption {
                        color: var(--text-secondary);
                        font-size: 0.875rem;
                        margin-bottom: 1rem;
                    }

                    .media-meta {
                        display: flex;
                        justify-content: space-between;
                        color: var(--text-secondary);
                        font-size: 0.75rem;
                    }

                    .modal {
                        display: none;
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        background: rgba(0, 0, 0, 0.8);
                        z-index: 1000;
                        overflow-y: auto;
                    }

                    .modal-content {
                        background: var(--surface);
                        margin: 3rem auto;
                        max-width: 800px;
                        border-radius: 1rem;
                        overflow: hidden;
                    }

                    .modal-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: 1.25rem;
                        border-bottom: 1px solid var(--border);
                    }

                    .modal-title {
                        font-size: 1.5rem;
                        font-weight: 600;
                    }

                    .modal-close {
                        background: none;
                        border: none;
                        color: var(--text-secondary);
                        font-size: 1.5rem;
                        cursor: pointer;
                    }

                    .modal-body {
                        padding: 1.25rem;
                    }

                    .modal-media {
                        width: 100%;
                        max-height: 500px;
                        object-fit: contain;
                        border-radius: 0.5rem;
                        margin-bottom: 1.25rem;
                    }

                    .modal-caption {
                        color: var(--text-secondary);
                        margin-bottom: 1.25rem;
                    }

                    .modal-metadata {
                        display: flex;
                        gap: 1rem;
                        color: var(--text-secondary);
                        margin-bottom: 1.25rem;
                    }

                    .interaction-bar {
                        display: flex;
                        gap: 1.25rem;
                        padding-top: 1.25rem;
                        border-top: 1px solid var(--border);
                    }

                    .rating-form {
                        display: flex;
                        align-items: center;
                        gap: 0.5rem;
                    }

                    .comments-section {
                        margin-top: 1.5rem;
                    }

                    .comment-form {
                        display: flex;
                        gap: 0.5rem;
                        margin-bottom: 1.25rem;
                    }

                    .comment-input {
                        flex: 1;
                        padding: 0.75rem 1rem;
                        border-radius: 0.5rem;
                        border: 1px solid var(--border);
                        background: var(--surface);
                    }

                    .comment {
                        background: var(--background);
                        padding: 1rem;
                        border-radius: 0.5rem;
                        margin-bottom: 1rem;
                    }

                    .comment-meta {
                        display: flex;
                        justify-content: space-between;
                        color: var(--text-secondary);
                        font-size: 0.75rem;
                        margin-bottom: 0.5rem;
                    }

                    .avg-rating {
                        display: flex;
                        align-items: center;
                        gap: 0.25rem;
                    }

                    .stars {
                        color: #f59e0b;
                    }

                    .no-results {
                        text-align: center;
                        padding: 3rem 0;
                        color: var(--text-secondary);
                    }

                    .alert {
                        max-width: 1280px;
                        margin: 1.25rem auto;
                        padding: 1rem;
                        border-radius: 0.5rem;
                    }

                    .alert-success {
                        background-color: rgba(34, 197, 94, 0.1);
                        color: var(--success);
                        border: 1px solid var(--success);
                    }

                    .alert-error {
                        background-color: rgba(239, 68, 68, 0.1);
                        color: var(--error);
                        border: 1px solid var(--error);
                    }

                    .btn {
                        padding: 0.5rem 1rem;
                        border-radius: 9999px;
                        background: var(--primary);
                        color: white;
                        border: none;
                        font-weight: 600;
                        transition: all 0.3s ease;
                    }

                    .btn:hover {
                        background: var(--primary-hover);
                    }

                    select {
                        padding: 0.75rem 1rem;
                        border-radius: 0.5rem;
                        border: 1px solid var(--border);
                        background: var(--surface);
                    }
                </style>
            </head>
            <body>
                <header class="header">
                    <div class="header-container">
                        <a href="{{ url_for('dashboard') }}" class="logo">
                            <i class="fas fa-photo-film"></i> StreamScape
                        </a>
                        <nav class="nav-links">
                            <a href="{{ url_for('dashboard') }}" class="nav-link active">
                                <i class="fas fa-home"></i> Dashboard
                            </a>
                            <a href="{{ url_for('logout') }}" class="nav-link">
                                <i class="fas fa-sign-out-alt"></i> Logout
                            </a>
                        </nav>
                    </div>
                </header>

                <div class="search-container">
                    {% with messages = get_flashed_messages(with_categories=true) %}
                        {% if messages %}
                            {% for category, message in messages %}
                                <div class="alert alert-{{ category }}">{{ message }}</div>
                            {% endfor %}
                        {% endif %}
                    {% endwith %}
                    <form class="search-form" method="POST" action="{{ url_for('dashboard') }}">
                        <input type="text" name="search_query" placeholder="Search for media..." class="search-input" value="{{ request.form.get('search_query', '') }}">
                        <button type="submit" class="search-btn">Search</button>
                    </form>
                </div>

                <div class="media-grid">
                    {% if media %}
                        {% for item in media %}
                            <div class="media-item" onclick="openModal({{ item.id }})">
                                {% if item.media_type == 'video' %}
                                    <video class="media-preview" poster="{{ item.file_path }}?format=jpg">
                                        <source src="{{ item.file_path }}" type="video/mp4">
                                    </video>
                                {% else %}
                                    <img src="{{ item.file_path }}" alt="{{ item.title }}" class="media-preview">
                                {% endif %}
                                <div class="media-info">
                                    <h3 class="media-title">{{ item.title | e }}</h3>
                                    <p class="media-caption">{{ item.caption | e }}</p>
                                    <div class="media-meta">
                                        <div class="avg-rating">
                                            <i class="fas fa-star stars"></i>
                                            {% set rating_sum = namespace(value=0) %}
                                            {% for rating in item.ratings %}
                                                {% set rating_sum.value = rating_sum.value + rating.value %}
                                            {% endfor %}
                                            {% if item.ratings|length > 0 %}
                                                {{ (rating_sum.value / item.ratings|length) | round(1) }}
                                            {% else %}
                                                No ratings
                                            {% endif %}
                                        </div>
                                        <span>{{ item.comments|length }} comments</span>
                                    </div>
                                </div>
                            </div>

                            <div id="modal-{{ item.id }}" class="modal">
                                <div class="modal-content">
                                    <div class="modal-header">
                                        <h2 class="modal-title">{{ item.title | e }}</h2>
                                        <button class="modal-close" onclick="closeModal({{ item.id }})">×</button>
                                    </div>
                                    <div class="modal-body">
                                        {% if item.media_type == 'video' %}
                                            <video class="modal-media" controls>
                                                <source src="{{ item.file_path }}" type="video/mp4">
                                            </video>
                                        {% else %}
                                            <img src="{{ item.file_path }}" alt="{{ item.title }}" class="modal-media">
                                        {% endif %}
                                        <p class="modal-caption">{{ item.caption | e }}</p>
                                        <div class="modal-metadata">
                                            {% if item.location %}
                                                <div><i class="fas fa-map-marker-alt"></i> {{ item.location | e }}</div>
                                            {% endif %}
                                            {% if item.people_present %}
                                                <div><i class="fas fa-users"></i> {{ item.people_present | e }}</div>
                                            {% endif %}
                                            <div><i class="fas fa-calendar"></i> {{ item.upload_date.strftime('%B %d, %Y') }}</div>
                                        </div>
                                        <div class="interaction-bar">
                                            <form class="rating-form" method="POST" action="{{ url_for('rate') }}">
                                                <input type="hidden" name="media_id" value="{{ item.id }}">
                                                <select name="value" required>
                                                    <option value="">Rate this</option>
                                                    <option value="1">1 - Poor</option>
                                                    <option value="2">2 - Fair</option>
                                                    <option value="3">3 - Good</option>
                                                    <option value="4">4 - Very Good</option>
                                                    <option value="5">5 - Excellent</option>
                                                </select>
                                                <button type="submit" class="btn">Rate</button>
                                            </form>
                                        </div>
                                        <div class="comments-section">
                                            <h3>Comments ({{ item.comments|length }})</h3>
                                            <form class="comment-form" method="POST" action="{{ url_for('comment') }}">
                                                <input type="hidden" name="media_id" value="{{ item.id }}">
                                                <input type="text" name="text" placeholder="Add a comment..." class="comment-input" required>
                                                <button type="submit" class="btn">Post</button>
                                            </form>
                                            {% if item.comments %}
                                                {% for comment in item.comments %}
                                                    <div class="comment">
                                                        <div class="comment-meta">
                                                            <span>User #{{ comment.user_id }}</span>
                                                            <span>{{ comment.date.strftime('%B %d, %Y') }}</span>
                                                        </div>
                                                        <p>{{ comment.text | e }}</p>
                                                    </div>
                                                {% endfor %}
                                            {% else %}
                                                <p>No comments yet.</p>
                                            {% endif %}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        {% endfor %}
                    {% else %}
                        <div class="no-results">
                            <i class="fas fa-search" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                            <h2>No results found</h2>
                            <p>Try different keywords.</p>
                        </div>
                    {% endif %}
                </div>

                <script>
                    function openModal(id) {
                        document.getElementById('modal-' + id).style.display = 'block';
                        document.body.style.overflow = 'hidden';
                    }

                    function closeModal(id) {
                        document.getElementById('modal-' + id).style.display = 'none';
                        document.body.style.overflow = 'auto';
                    }

                    window.onclick = function(event) {
                        if (event.target.classList.contains('modal')) {
                            event.target.style.display = 'none';
                            document.body.style.overflow = 'auto';
                        }
                    }
                </script>
            </body>
            </html>
        ''', media=media)

@app.route('/upload', methods=['POST'])
def upload():
    if 'user_id' not in session or session['role'] != 'creator':
        return redirect(url_for('login'))

    title = request.form['title']
    caption = request.form['caption']
    location = request.form['location']
    people_present = request.form['people_present']
    file = request.files['file']
    media_type = request.form['media_type']

    if file:
        filename = f"{uuid.uuid4()}_{file.filename}"
        blob_client = blob_service_client.get_blob_client(container=AZURE_CONTAINER_NAME, blob=filename)
        blob_client.upload_blob(file, overwrite=True, content_settings=ContentSettings(
            content_type='video/mp4' if media_type == 'video' else 'image/jpeg'))
        blob_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_CONTAINER_NAME}/{filename}"

        media = Media(
            title=title,
            caption=caption,
            location=location,
            people_present=people_present,
            file_path=blob_url,
            media_type=media_type,
            creator_id=session['user_id']
        )
        db.session.add(media)
        db.session.commit()
        flash('Media uploaded successfully!', 'success')
    else:
        flash('No file selected!', 'error')

    return redirect(url_for('dashboard'))

@app.route('/comment', methods=['POST'])
def comment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    text = request.form['text']
    media_id = request.form['media_id']

    comment = Comment(
        text=text,
        user_id=session['user_id'],
        media_id=media_id
    )
    db.session.add(comment)
    db.session.commit()
    flash('Comment added!', 'success')

    return redirect(url_for('dashboard'))

@app.route('/rate', methods=['POST'])
def rate():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    media_id = request.form['media_id']
    value = request.form['value']

    existing_rating = Rating.query.filter_by(user_id=session['user_id'], media_id=media_id).first()
    if existing_rating:
        flash('You have already rated this media!', 'error')
        return redirect(url_for('dashboard'))

    rating = Rating(
        value=value,
        user_id=session['user_id'],
        media_id=media_id
    )
    db.session.add(rating)
    db.session.commit()
    flash('Media rated!', 'success')

    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('role', None)
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run()