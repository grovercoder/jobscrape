from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from jobscrape.models import User, Resume
from jobscrape.db import DB
from jobscrape.backend.loginmanager import login_manager
from jobscrape.backend.form_user_signup import RegistrationForm

bp = Blueprint('main', __name__)
mydb = DB()
session = mydb.get_session()

@login_manager.user_loader
def load_user(user_id):
    return session.query(User).get(int(user_id))

class UserLogin(UserMixin):
    def __init__(self, user):
        self.id = user.id
        self.username = user.username


@bp.route('/', methods=["GET"])
def home_page():
    return render_template('index.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = session.query(User).filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(UserLogin(user))
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

    return render_template('login.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', username=current_user.username)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))


@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm()

    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        password = form.password.data

        # Check if username or email already exists
        existing_user = session.query(User).filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('main.signup'))

        new_user = User.create(email=email, username=username, password=password)
        session.add(new_user)
        session.commit()

        flash('Account created successfully! You can now login.', 'success')
        return redirect(url_for('main.login'))

    return render_template('signup.html', form=form)