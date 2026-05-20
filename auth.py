from datetime import datetime

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, current_app)
from flask_mail import Message
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import generate_password_hash, check_password_hash

from entities import db, User

bp = Blueprint('auth', __name__, url_prefix='/auth')

SALT_CONFIRM = 'email-confirm'
SALT_RESET   = 'password-reset'


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'])


def generate_token(email: str, salt: str) -> str:
    return _serializer().dumps(email, salt=salt)


def verify_token(token: str, salt: str, max_age: int = 86400):
    try:
        return _serializer().loads(token, salt=salt, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None


def send_email(to: str, subject: str, html: str):
    if not current_app.config.get('MAIL_USERNAME'):
        current_app.logger.warning('MAIL_USERNAME not set — skipping email send.')
        return
    try:
        from flask_mail import Mail
        mail: Mail = current_app.extensions['mail']
        msg = Message(subject=subject, recipients=[to], html=html)
        mail.send(msg)
    except Exception as e:
        current_app.logger.error('Failed to send email to %s: %s', to, e)


def confirmation_email_html(confirm_url: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;padding:32px;
                background:#fff;border-radius:12px;border:1px solid #eee;">
      <h2 style="color:#FF6B35;margin-bottom:8px;">🍳 RecipeHub</h2>
      <h3 style="color:#1a1a1a;">Confirm your email address</h3>
      <p style="color:#555;line-height:1.6;">
        Thank you for registering! Please click the button below to confirm
        your email address. The link expires in <strong>24 hours</strong>.
      </p>
      <a href="{confirm_url}"
         style="display:inline-block;margin:24px 0;padding:12px 28px;
                background:#FF6B35;color:#fff;border-radius:8px;
                text-decoration:none;font-weight:700;font-size:15px;">
        ✓ Confirm Email
      </a>
      <p style="color:#999;font-size:12px;">
        If you didn't create an account, simply ignore this message.
      </p>
    </div>"""


def reset_email_html(reset_url: str) -> str:
    return f"""
    <div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;padding:32px;
                background:#fff;border-radius:12px;border:1px solid #eee;">
      <h2 style="color:#FF6B35;margin-bottom:8px;">🍳 RecipeHub</h2>
      <h3 style="color:#1a1a1a;">Reset your password</h3>
      <p style="color:#555;line-height:1.6;">
        We received a request to reset the password for your account.
        Click the button below — the link expires in <strong>1 hour</strong>.
      </p>
      <a href="{reset_url}"
         style="display:inline-block;margin:24px 0;padding:12px 28px;
                background:#FF6B35;color:#fff;border-radius:8px;
                text-decoration:none;font-weight:700;font-size:15px;">
        🔑 Reset Password
      </a>
      <p style="color:#999;font-size:12px;">
        If you didn't request a password reset, you can safely ignore this email.
      </p>
    </div>"""


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        errors = []
        import re
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            errors.append('Invalid email address.')
        if len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if User.query.filter_by(email=email).first():
            errors.append('This email is already registered.')
        if User.query.filter_by(username=username).first():
            errors.append('This username is already taken.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return redirect(url_for('auth.register'))

        user = User(
            email              = email,
            username           = username,
            password_hash      = generate_password_hash(password),
            is_email_confirmed = False,
        )
        db.session.add(user)
        db.session.commit()

        token       = generate_token(email, SALT_CONFIRM)
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        send_email(email, 'Confirm your RecipeHub account',
                   confirmation_email_html(confirm_url))

        login_user(user)
        flash('Account created! Please check your email to confirm your address.', 'success')
        return redirect(url_for('index'))

    return render_template('register.html')


@bp.route('/confirm/<token>')
def confirm_email(token):
    email = verify_token(token, SALT_CONFIRM, max_age=86400)
    if not email:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('index'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Account not found.', 'danger')
        return redirect(url_for('index'))

    if user.is_email_confirmed:
        flash('Email already confirmed. You can log in.', 'info')
        return redirect(url_for('index'))

    user.is_email_confirmed = True
    user.email_confirmed_at = datetime.utcnow()
    db.session.commit()
    flash('✓ Email confirmed successfully! Welcome to RecipeHub.', 'success')
    return redirect(url_for('index'))


@bp.route('/resend-confirmation')
@login_required
def resend_confirmation():
    if current_user.is_email_confirmed:
        flash('Your email is already confirmed.', 'info')
        return redirect(url_for('index'))

    token       = generate_token(current_user.email, SALT_CONFIRM)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    send_email(current_user.email,
               'Confirm your RecipeHub account',
               confirmation_email_html(confirm_url))
    flash('Confirmation email resent. Please check your inbox.', 'info')
    return redirect(url_for('index'))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user     = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('auth.login'))

        if not user.is_active:
            flash('Your account has been disabled. Contact an administrator.', 'danger')
            return redirect(url_for('auth.login'))

        login_user(user)
        next_page = request.args.get('next')
        flash('Logged in successfully.', 'success')
        return redirect(next_page or url_for('index'))

    return render_template('login.html')


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = User.query.filter_by(email=email).first()

        flash('If that email is registered, a reset link has been sent.', 'info')

        if user:
            token     = generate_token(email, SALT_RESET)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            send_email(email, 'Reset your RecipeHub password',
                       reset_email_html(reset_url))

        return redirect(url_for('auth.forgot_password'))

    return render_template('forgot_password.html')


@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_token(token, SALT_RESET, max_age=3600)
    if not email:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Account not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(request.url)
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(request.url)

        user.password_hash = generate_password_hash(password)
        db.session.commit()
        flash('✓ Password updated successfully. You can now log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('reset_password.html', token=token)
