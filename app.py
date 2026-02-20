import os
from decimal import Decimal
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, SubmitField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange
from math import exp, log
import logging
from flask_wtf.csrf import CSRFProtect

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
if not app.config['SECRET_KEY']:
    if os.environ.get('FLASK_ENV') == 'production':
        raise ValueError('SECRET_KEY environment variable must be set in production')
    app.config['SECRET_KEY'] = 'dev-secret-change-me'

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///market.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_ENV'] = os.environ.get('FLASK_ENV', 'production')
app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'

# Security
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Initialize CSRF protection
#CSRFProtect(app)

db = SQLAlchemy(app)
login = LoginManager(app)
login.login_view = 'login'

# Liquidity parameter for LMSR
B = float(os.environ.get('LMSR_B', '10.0'))  # adjust for liquidity

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    balance = db.Column(db.Float, default=100.0)  # start with demo balance
    is_admin = db.Column(db.Boolean, default=False)
    holdings_yes = db.Column(db.Float, default=0.0)
    holdings_no = db.Column(db.Float, default=0.0)

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)

    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    side = db.Column(db.String(10))  # 'yes' or 'no'
    qty = db.Column(db.Float)
    cost = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, server_default=db.func.now())

class MarketState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    q_yes = db.Column(db.Float, default=0.0)
    q_no = db.Column(db.Float, default=0.0)
    resolved = db.Column(db.Boolean, default=False)
    outcome = db.Column(db.String(10), nullable=True)  # 'yes' or 'no' or None

# Forms
class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=4)])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class BuyForm(FlaskForm):
    side = StringField('Side', validators=[DataRequired()])
    qty = DecimalField('Quantity', validators=[DataRequired(), NumberRange(min=0.01)])
    submit = SubmitField('Buy')

class ResolveForm(FlaskForm):
    outcome = StringField('Outcome', validators=[DataRequired()])
    submit = SubmitField('Resolve')

# Helpers
@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_market():
    m = MarketState.query.first()
    if not m:
        m = MarketState(q_yes=0.0, q_no=0.0, resolved=False)
        db.session.add(m)
        db.session.commit()
    return m

def cost_function(q_yes, q_no):
    # C(q) = b * ln(exp(q_yes/b) + exp(q_no/b))
    a = exp(q_yes / B)
    b = exp(q_no / B)
    return B * log(a + b)

def price_yes(q_yes, q_no):
    a = exp(q_yes / B)
    b = exp(q_no / B)
    return a / (a + b)

# Routes
@app.route('/')
def index():
    market = get_market()
    p_yes = price_yes(market.q_yes, market.q_no)
    p_no = 1 - p_yes
    return render_template('index.html', market=market, p_yes=p_yes, p_no=p_no)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username taken')
            return redirect(url_for('register'))
        u = User(username=form.username.data)
        u.set_password(form.password.data)
        # Make first registered user admin if ADMIN_USERNAME matches
        admin_name = os.environ.get('ADMIN_USERNAME')
        if admin_name and u.username == admin_name:
            u.is_admin = True
        db.session.add(u)
        db.session.commit()
        flash('Registered. You have demo balance of 100.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(username=form.username.data).first()
        if u and u.check_password(form.password.data):
            login_user(u)
            return redirect(url_for('index'))
        flash('Invalid credentials')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/buy', methods=['POST'])
@login_required
def buy():
    form = BuyForm()
    if not form.validate_on_submit():
        flash('Invalid order')
        return redirect(url_for('index'))
    side = form.side.data.lower()
    qty = float(form.qty.data)
    if qty <= 0:
        flash('Quantity must be positive')
        return redirect(url_for('index'))
    market = get_market()
    if market.resolved:
        flash('Market already resolved')
        return redirect(url_for('index'))

    # compute cost = C(q + delta) - C(q)
    if side == 'yes':
        new_q_yes = market.q_yes + qty
        new_q_no = market.q_no
    elif side == 'no':
        new_q_yes = market.q_yes
        new_q_no = market.q_no + qty
    else:
        flash('Side must be yes or no')
        return redirect(url_for('index'))

    cost_before = cost_function(market.q_yes, market.q_no)
    cost_after = cost_function(new_q_yes, new_q_no)
    cost = cost_after - cost_before

    if current_user.balance < cost:
        flash(f'Insufficient balance. Cost {cost:.4f}')
        return redirect(url_for('index'))

    # apply trade
    current_user.balance -= cost
    if side == 'yes':
        current_user.holdings_yes += qty
        market.q_yes = new_q_yes
    else:
        current_user.holdings_no += qty
        market.q_no = new_q_no

    trade = Trade(user_id=current_user.id, side=side, qty=qty, cost=cost)
    db.session.add(trade)
    db.session.commit()
    flash(f'Bought {qty} {side} for {cost:.4f}')
    return redirect(url_for('index'))

@app.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)

# Admin routes
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated

@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    market = get_market()
    trades = Trade.query.order_by(Trade.timestamp.desc()).limit(200).all()
    users = User.query.all()
    return render_template('admin.html', market=market, trades=trades, users=users)

@app.route('/admin/resolve', methods=['POST'])
@login_required
@admin_required
def admin_resolve():
    form = ResolveForm()
    #if not form.validate_on_submit():
        #flash('Invalid resolve')
        #return redirect(url_for('admin_panel'))
    outcome = form.outcome.data.lower()
    if outcome not in ('yes', 'no'):
        flash('Outcome must be yes or no')
        return redirect(url_for('admin_panel'))
    market = get_market()
    if market.resolved:
        flash('Market already resolved')
        return redirect(url_for('admin_panel'))

    # settle: pay 1 unit per winning share to holders
    if outcome == 'yes':
        for u in User.query.all():
            payout = u.holdings_yes * 1.0
            u.balance += payout
            # zero holdings
            u.holdings_yes = 0.0
            u.holdings_no = 0.0
    else:
        for u in User.query.all():
            payout = u.holdings_no * 1.0
            u.balance += payout
            u.holdings_yes = 0.0
            u.holdings_no = 0.0

    market.resolved = True
    market.outcome = outcome
    db.session.commit()
    flash(f'Market resolved: {outcome}')
    return redirect(url_for('admin_panel'))

# Utility route to reset market (admin)
@app.route('/admin/reset', methods=['POST'])
@login_required
@admin_required
def admin_reset():
    # reset market and zero holdings (for demo)
    market = get_market()
    market.q_yes = 0.0
    market.q_no = 0.0
    market.resolved = False
    market.outcome = None
    for u in User.query.all():
        u.holdings_yes = 0.0
        u.holdings_no = 0.0
    db.session.commit()
    flash('Market reset')
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)
    
    # create DB if needed
    with app.app_context():
        db.create_all()
        # create admin user if env vars provided
        admin_name = os.environ.get('ADMIN_USERNAME')
        admin_pw = os.environ.get('ADMIN_PASSWORD')
        if admin_name and admin_pw:
            if not User.query.filter_by(username=admin_name).first():
                u = User(username=admin_name, is_admin=True, balance=1000.0)
                u.set_password(admin_pw)
                db.session.add(u)
                db.session.commit()
    
    # Use environment variables for host and port
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    app.run(host=host, port=port, debug=app.config['DEBUG'])