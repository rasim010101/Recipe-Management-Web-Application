# auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        username = request.form['username'].strip()
        password = request.form['password']
        if User.query.filter_by(email=email).first():
            flash('Email is already registered','warning'); return redirect(url_for('auth.register'))
        if User.query.filter_by(username=username).first():
            flash('Username is already taken','warning'); return redirect(url_for('auth.register'))
        user = User(email=email, username=username, password_hash=generate_password_hash(password))
        db.session.add(user); db.session.commit()
        login_user(user)
        flash('Registration successful','success')
        return redirect(url_for('index'))
    return render_template('register.html')

@bp.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password','danger'); return redirect(url_for('auth.login'))
        login_user(user)
        flash('Logged in successfully','success')
        return redirect(url_for('index'))
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out','info')
    return redirect(url_for('index'))
