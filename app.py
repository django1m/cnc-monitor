from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from smb.SMBConnection import SMBConnection
import os
import pandas as pd
from datetime import datetime
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cnc_visualizer.db'
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

class CNCMachine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)
    working_hours_start = db.Column(db.String(5), default='08:00')
    working_hours_end = db.Column(db.String(5), default='17:00')
    working_days = db.Column(db.String(20), default='0,1,2,3,4')  # 0=Monday, 6=Sunday

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def fetch_cnc_data(machine):
    try:
        conn = SMBConnection('admin', '', 'client', 'server', use_ntlm_v2=True)
        conn.connect(machine.ip_address, 139)
        
        # Create directory if it doesn't exist
        local_dir = f'/tmp/CNC_{machine.id}'
        os.makedirs(local_dir, exist_ok=True)
        
        # Fetch JobHistory.csv
        with open(f'{local_dir}/JobHistory.csv', 'wb') as file:
            conn.retrieveFile('hdd1', '/JobHistory.csv', file)
            
        # Fetch files from PastJobHistory
        files = conn.listPath('hdd1', '/PastJobHistory')
        for f in files:
            if f.filename.endswith('.csv'):
                with open(f'{local_dir}/{f.filename}', 'wb') as file:
                    conn.retrieveFile('hdd1', f'/PastJobHistory/{f.filename}', file)
                    
        conn.close()
        return True
    except Exception as e:
        print(f"Error fetching data for {machine.name}: {str(e)}")
        return False

def calculate_kpis():
    machines = CNCMachine.query.all()
    kpis = {}
    
    for machine in machines:
        try:
            df = pd.read_csv(f'/tmp/CNC_{machine.id}/JobHistory.csv')
            total_time = df['Duration'].sum()
            movement_time = df['MovementTime'].sum()
            if total_time > 0:
                occupation_rate = (movement_time / total_time) * 100
            else:
                occupation_rate = 0
                
            kpis[machine.name] = {
                'occupation_rate': round(occupation_rate, 2),
                'total_jobs': len(df),
                'total_time': round(total_time / 3600, 2)  # Convert to hours
            }
        except Exception as e:
            kpis[machine.name] = {
                'occupation_rate': 0,
                'total_jobs': 0,
                'total_time': 0
            }
            
    return kpis

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
@login_required
def dashboard():
    machines = CNCMachine.query.all()
    kpis = calculate_kpis()
    return render_template('dashboard.html', machines=machines, kpis=kpis)

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if not current_user.is_admin:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        data = request.json
        if data['action'] == 'add_machine':
            machine = CNCMachine(
                name=data['name'],
                ip_address=data['ip_address']
            )
            db.session.add(machine)
            db.session.commit()
        elif data['action'] == 'update_machine':
            machine = CNCMachine.query.get(data['id'])
            if machine:
                machine.name = data['name']
                machine.ip_address = data['ip_address']
                machine.working_hours_start = data['working_hours_start']
                machine.working_hours_end = data['working_hours_end']
                machine.working_days = data['working_days']
                db.session.commit()
                
    machines = CNCMachine.query.all()
    return render_template('settings.html', machines=machines)

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: [fetch_cnc_data(m) for m in CNCMachine.query.all()],
                 trigger="interval",
                 minutes=60)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='admin', is_admin=True)
            db.session.add(admin)
            db.session.commit()
    scheduler.start()
    app.run(host='0.0.0.0', port=5000)
